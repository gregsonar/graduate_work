# subscriptions/api/v1/subscription.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from subscriptions.db.postgres import get_session
from subscriptions.services.subscription_service import SubscriptionService
from subscriptions.schemas.subscription_schema import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionSuspend,
    SubscriptionResume,
    SubscriptionCancel,
    SubscriptionHistoryResponse,
    DetailResponse
)
from subscriptions.core.config import settings
router = APIRouter()

@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new subscription",
    description="Creates a new subscription for a user"
)
async def create_subscription(
    subscription: SubscriptionCreate,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    print(settings)
    return await subscription_service.create_subscription(subscription)

@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription details",
    description="Returns detailed information about a specific subscription"
)
async def get_subscription(
    subscription_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    return await subscription_service.get_subscription(subscription_id)

@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update subscription",
    description="Updates subscription details"
)
async def update_subscription(
    subscription_id: UUID,
    update_data: SubscriptionUpdate,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    return await subscription_service.update_subscription(subscription_id, update_data)

@router.post(
    "/{subscription_id}/suspend",
    response_model=DetailResponse,
    summary="Suspend subscription",
    description="Temporarily suspends an active subscription"
)
async def suspend_subscription(
    subscription_id: UUID,
    suspend_data: SubscriptionSuspend,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    await subscription_service.suspend_subscription(subscription_id, suspend_data.reason)
    return DetailResponse(detail="Subscription suspended successfully", code="SUSPENDED")

@router.post(
    "/{subscription_id}/resume",
    response_model=DetailResponse,
    summary="Resume subscription",
    description="Resumes a suspended subscription"
)
async def resume_subscription(
    subscription_id: UUID,
    resume_data: SubscriptionResume,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    await subscription_service.resume_subscription(subscription_id, resume_data.comment)
    return DetailResponse(detail="Subscription resumed successfully", code="RESUMED")

@router.post(
    "/{subscription_id}/cancel",
    response_model=DetailResponse,
    summary="Cancel subscription",
    description="Cancels an active subscription"
)
async def cancel_subscription(
    subscription_id: UUID,
    cancel_data: SubscriptionCancel,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    await subscription_service.cancel_subscription(
        subscription_id,
        cancel_data.reason,
        cancel_data.immediate
    )
    return DetailResponse(detail="Subscription cancelled successfully", code="CANCELLED")

@router.get(
    "/{subscription_id}/history",
    response_model=List[SubscriptionHistoryResponse],
    summary="Get subscription history",
    description="Returns the history of changes for a subscription"
)
async def get_subscription_history(
    subscription_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    subscription_service = SubscriptionService(session)
    return await subscription_service.get_subscription_history(subscription_id)
