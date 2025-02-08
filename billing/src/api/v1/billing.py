from uuid import UUID
from http import HTTPStatus

from fastapi import APIRouter, Depends, Response

from billing.src.schemas.tariff_schemas import PaymentSchema
from billing.src.services.billing_service import BillingService, get_billing_service
from billing.src.api.dependencies import get_current_user
from billing.src.schemas.payment_schemas import CreatedPaymentSchema, CreatePaymentSchema




router = APIRouter()


@router.post('/subscribe',
             summary="Подписка",
             response_description="Ссылка на оплату",
             response_model=CreatedPaymentSchema,
             status_code=HTTPStatus.CREATED)
async def subscribe(
        payment_data: CreatePaymentSchema,
        user_data=Depends(get_current_user),
        payment_service: BillingService = Depends(get_billing_service)
) -> CreatedPaymentSchema:
    return await payment_service.create_payment(user_data.user_id, payment_data.tariff_id)


@router.get('/history',
            summary="История платежей",
            response_model=list[PaymentSchema],
            status_code=HTTPStatus.OK)
async def history(
        user_data=Depends(get_current_user),
        payment_service: BillingService = Depends(get_billing_service),
) -> list[PaymentSchema]:
    return await payment_service.get_all_payments(user_data.user_id)
