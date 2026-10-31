from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from backend.app.config import Settings, get_settings


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    subject: str
    role: str


def get_current_citizen(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Actor:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "authentication_required", "message": "A valid citizen token is required."},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except InvalidTokenError:
        raise unauthorized from None

    subject = claims.get("sub")
    role = claims.get("role")
    if not isinstance(subject, str) or not subject.strip() or role != "citizen":
        raise unauthorized
    return Actor(subject=subject, role=role)


def get_current_analyst_reviewer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Actor:
    """Require an explicit reviewer capability from the trusted JWT issuer.

    The project must grant this capability only to staff authorized for the
    review queue. It deliberately does not infer reviewer access from a citizen
    token or from a broad administrator role.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "authentication_required", "message": "A valid staff token is required."},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except InvalidTokenError:
        raise unauthorized from None

    subject = claims.get("sub")
    role = claims.get("role")
    permissions = claims.get("permissions", [])
    if not isinstance(subject, str) or not subject.strip() or role == "citizen":
        raise unauthorized
    if not isinstance(permissions, list) or "complaint_analysis:review" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "review_permission_required", "message": "Complaint analysis review access is required."},
        )
    return Actor(subject=subject, role=role if isinstance(role, str) else "staff")

def _get_current_staff_with_permission(
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
    permission: str,
) -> Actor:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "authentication_required", "message": "A valid staff token is required."},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except InvalidTokenError:
        raise unauthorized from None
    subject = claims.get("sub")
    role = claims.get("role")
    permissions = claims.get("permissions", [])
    if not isinstance(subject, str) or not subject.strip() or role == "citizen":
        raise unauthorized
    if not isinstance(permissions, list) or permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "permission_required", "message": f"The {permission} permission is required."},
        )
    return Actor(subject=subject, role=role if isinstance(role, str) else "staff")


def get_current_resolution_officer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Actor:
    return _get_current_staff_with_permission(credentials, settings, "complaint:resolve")


def get_current_independent_verification_reviewer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Actor:
    return _get_current_staff_with_permission(credentials, settings, "complaint_verification:review")

