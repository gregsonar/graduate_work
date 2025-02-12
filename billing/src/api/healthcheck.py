from fastapi import APIRouter, Response, status


router = APIRouter()


@router.get(
    "/health",
    tags=["healthcheck"],
    summary="Проверка состояния сервиса",
    response_description="Состояние сервиса",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
def healthcheck() -> Response:
    """Check if service healthy."""
    return Response(status_code=status.HTTP_200_OK, content="Its a live")