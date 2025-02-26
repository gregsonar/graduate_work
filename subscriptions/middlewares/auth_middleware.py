from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint
)
from starlette.responses import Response


@dataclass
class AuthConfig:
    """Configuration for authentication middleware"""

    secret_key: str
    public_paths: List[str] = None
    token_prefix: str = "Bearer"
    algorithm: str = "HS256"


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        self.public_paths = config.public_paths or [
            "/openapi",
            "/openapi.json",
            "/docs",
            "/redoc",
            "/health",
        ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Get the full path including scope's root_path
        root_path = request.scope.get("root_path", "").rstrip("/")
        path = request.url.path
        full_path = f"{root_path}{path}"

        # Debug logging
        print(f"Checking path: {full_path}")
        print(f"Public paths: {self.public_paths}")

        # Check if path is public using exact matching
        if full_path in self.public_paths or path in self.public_paths:
            return await call_next(request)

        # Also check if path ends with any of the default doc paths
        default_doc_paths = ["/openapi", "/openapi.json", "/docs", "/redoc"]
        if any(full_path.endswith(doc_path) for doc_path in default_doc_paths):
            return await call_next(request)

        try:
            # Get and validate auth header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401, detail="Missing authentication header"
                )

            # Validate token format
            if not auth_header.startswith(self.config.token_prefix):
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid token format. Must start with '{self.config.token_prefix}'",
                )

            # Extract and verify token
            token = auth_header.replace(f"{self.config.token_prefix} ", "")
            try:
                payload = jwt.decode(
                    token, self.config.secret_key, algorithms=[self.config.algorithm]
                )

                # Check token expiration
                exp = payload.get("exp")
                if exp and datetime.utcnow().timestamp() > exp:
                    raise HTTPException(status_code=401, detail="Token has expired")

                # Add decoded payload to request state
                request.state.user = payload

            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid token")

            return await call_next(request)

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )
