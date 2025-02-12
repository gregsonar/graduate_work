import logging

import httpx
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

logger = logging.getLogger(__name__)

oauth2_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT token authentication"
)


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
):
    """Get current user from auth service"""
    authorization = f"{credentials.scheme} {credentials.credentials}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://auth_api:8000/api/v1/auth/me",
                headers={"Authorization": authorization}
            )

            logger.info(f"Auth service response status: {response.status_code}")
            logger.info(f"Auth service response body: {response.text}")

            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )

            try:
                user_data = response.json()
                logger.info(f"Parsed user data: {user_data}")
                return user_data
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid response from auth service"
                )

        except httpx.RequestError as e:
            logger.error(f"Request to auth service failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service is unavailable"
            )


async def get_admin_user(current_user=Depends(get_current_user)):
    if not any(role in ["admin", "superuser"] for role in current_user["roles"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user