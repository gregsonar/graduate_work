from http import HTTPStatus

from fastapi import APIRouter, Depends

from billing.src.schemas.tariff_schemas import TariffSchema
from billing.src.services.tariff_service import (
    TariffService,
    get_tariff_service
)

router = APIRouter()


@router.get(
    "/tariffs",
    summary="Получить активные тарифы",
    response_description="Активные тарифы",
    response_model=list[TariffSchema],
    status_code=HTTPStatus.OK,
)
async def get_tariffs(
    tariff_service: TariffService = Depends(get_tariff_service),
) -> list[TariffSchema]:
    return await tariff_service.get_active_tariffs()
