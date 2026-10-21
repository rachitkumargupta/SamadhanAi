import asyncio
import json
import unittest

from backend.app.middleware import RequestBodyLimitMiddleware


class RequestBodyLimitMiddlewareTests(unittest.TestCase):
    def test_chunked_oversized_upload_is_rejected_before_endpoint(self):
        downstream_called = False
        sent = []

        async def endpoint(scope, receive, send):
            nonlocal downstream_called
            downstream_called = True
            while (message := await receive()).get("type") == "http.request":
                if not message.get("more_body"):
                    break

        middleware = RequestBodyLimitMiddleware(
            endpoint,
            path="/api/v1/complaints",
            method="POST",
            maximum_bytes=5,
        )
        scope = {
            "type": "http",
            "path": "/api/v1/complaints",
            "method": "POST",
            "headers": [(b"transfer-encoding", b"chunked")],
            "state": {"correlation_id": "test-correlation"},
        }
        messages = iter(
            [
                {"type": "http.request", "body": b"1234", "more_body": True},
                {"type": "http.request", "body": b"5678", "more_body": False},
            ]
        )

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        asyncio.run(middleware(scope, receive, send))
        self.assertTrue(downstream_called)
        response_start = next(message for message in sent if message["type"] == "http.response.start")
        response_body = next(message for message in sent if message["type"] == "http.response.body")
        self.assertEqual(response_start["status"], 413)
        self.assertIn((b"x-correlation-id", b"test-correlation"), response_start["headers"])
        body = json.loads(response_body["body"])
        self.assertEqual(body["error"]["code"], "request_too_large")


if __name__ == "__main__":
    unittest.main()
