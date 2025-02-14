from http import HTTPStatus

from fastapi import APIRouter, Depends

from billing.src.services.tariff_service import get_tariff_service, TariffService
from billing.src.schemas.tariff_schemas import TariffSchema


router = APIRouter()


@router.get(
    "/tariffs",
    summary="Получить активные тарифы",
    response_description="Активные тарифы",
    response_model=list[TariffSchema],
    status_code=HTTPStatus.OK
)
async def get_tariffs(
        tariff_service: TariffService = Depends(get_tariff_service)
) -> list[TariffService]:
    return await tariff_service.get_active_tariffs()