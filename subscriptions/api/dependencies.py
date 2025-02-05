from fastapi import Depends, Header, HTTPException, status
import httpx


async def get_current_user(authorization: str = Header(...)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://auth_api:8000/api/v1/auth/me",
            headers={"Authorization": authorization}
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        return response.json()


async def get_admin_user(current_user=Depends(get_current_user)):
    if not any(role in ["admin", "superuser"] for role in current_user["roles"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user