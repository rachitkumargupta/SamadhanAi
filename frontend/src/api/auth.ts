// Native WebCrypto HS256 Token Generator & Auth State
export interface UserSession {
  subject: string;
  role: 'citizen' | 'officer';
  name: string;
  token: string;
}

export const DEFAULT_JWT_SECRET = "replace-with-a-random-secret-of-at-least-32-bytes";
export const DEFAULT_JWT_ISSUER = "https://identity.example.invalid";
export const DEFAULT_JWT_AUDIENCE = "samadhan-api";

export async function generateDevToken(
  subject: string,
  role: 'citizen' | 'officer',
  secret: string = DEFAULT_JWT_SECRET,
  issuer: string = DEFAULT_JWT_ISSUER,
  audience: string = DEFAULT_JWT_AUDIENCE
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "HS256", typ: "JWT" };
  
  const payload = {
    sub: subject,
    role: role,
    iss: issuer,
    aud: audience,
    iat: now,
    exp: now + 30 * 24 * 60 * 60, // 30 days
    ...(role === 'officer' ? { permissions: ["complaint_analysis:review"] } : {})
  };

  const enc = new TextEncoder();
  const b64Url = (buf: ArrayBuffer | Uint8Array) =>
    btoa(String.fromCharCode(...new Uint8Array(buf)))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

  const headerB64 = b64Url(enc.encode(JSON.stringify(header)));
  const payloadB64 = b64Url(enc.encode(JSON.stringify(payload)));
  const data = enc.encode(`${headerB64}.${payloadB64}`);

  try {
    const key = await crypto.subtle.importKey(
      "raw",
      enc.encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const sig = await crypto.subtle.sign("HMAC", key, data);
    return `${headerB64}.${payloadB64}.${b64Url(sig)}`;
  } catch {
    // Fallback simple token if crypto unavailable
    return `${headerB64}.${payloadB64}.mock_signature`;
  }
}
