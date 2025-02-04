from fastapi import Depends
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.postgres import get_async_session
from models.tariffs import TariffModel
from schemas.tariff_schemas import TariffSchema


class TariffService:

    def __init__(self, session):
        self.session = session

    async def get_active_tariffs(self) -> list[TariffSchema]:
        query = await self.session.execute(
            select(TariffModel).where(TariffModel.is_active == True)
        )
        tariff_list = []
        for tariff in query.scalars().all():
            tariff_list.append(
                TariffSchema(
                    id=tariff.id,
                    name=tariff.name,
                    description=tariff.description,
                    price=tariff.price
                )
            )
        return tariff_list


def get_tariff_service(
        session: AsyncSession = Depends(get_async_session)
):
    return TariffService(session)