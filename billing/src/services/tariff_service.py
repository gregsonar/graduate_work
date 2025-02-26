from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from billing.src.db.postgres import get_session
from billing.src.models.tariffs import TariffModel
from billing.src.schemas.tariff_schemas import TariffSchema


class TariffService:

    def __init__(self, session):
        self.session = session

    async def get_active_tariffs(self) -> list[TariffSchema]:
        query = await self.session.execute(
            select(TariffModel).where(TariffModel.is_active)
        )
        tariff_list = []
        for tariff in query.scalars().all():
            tariff_list.append(
                TariffSchema(
                    id=tariff.id,
                    name=tariff.name,
                    description=tariff.description,
                    price=tariff.price,
                )
            )
        return tariff_list


def get_tariff_service(session: AsyncSession = Depends(get_session)):
    return TariffService(session)
