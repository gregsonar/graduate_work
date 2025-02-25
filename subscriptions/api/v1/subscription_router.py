import datetime
import logging
from uuid import UUID

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from subscriptions.core.config import settings
from subscriptions.db.postgres import get_session
from subscriptions.schemas.subscription_schema import (
    DetailResponse,
    SubscriptionCancel,
    SubscriptionCreate,
    SubscriptionHistoryResponse,
    SubscriptionResponse,
    SubscriptionResume,
    SubscriptionSuspend,
    SubscriptionUpdate,
)
from subscriptions.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
        data: SubscriptionCreate,
        session: AsyncSession = Depends(get_session)
):
    """Create a new subscription for the current user"""
    subscription_service = SubscriptionService(session)
    try:
        return await subscription_service.create_subscription(data)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid user data structure received from auth service"
        )
    except ValueError as e:
        logger.error(f"Failed to convert user ID to UUID. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
        subscription_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """Get subscription details"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(subscription_id)

    return subscription


@router.get("/user/{user_id}", response_model=SubscriptionResponse)
async def get_subscription_with_user_id(
        user_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """Get subscription details"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription_with_user_id(user_id)

    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
        subscription_id: UUID,
        data: SubscriptionUpdate,
        session: AsyncSession = Depends(get_session)
):
    """Update subscription details"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(subscription_id)

    return await subscription_service.update_subscription(subscription_id, data)


@router.post("/{subscription_id}/suspend", response_model=DetailResponse)
async def suspend_subscription(
        subscription_id: UUID,
        data: SubscriptionSuspend,
        session: AsyncSession = Depends(get_session)
):
    """Suspend an active subscription"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(subscription_id)

    await subscription_service.suspend_subscription(subscription_id, data.reason)
    return DetailResponse(
        detail="Subscription suspended successfully",
        code="SUBSCRIPTION_SUSPENDED"
    )


@router.post("/{subscription_id}/resume", response_model=DetailResponse)
async def resume_subscription(
        subscription_id: UUID,
        data: SubscriptionResume,
        session: AsyncSession = Depends(get_session)
):
    """Resume a suspended subscription"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(subscription_id)

    await subscription_service.resume_subscription(subscription_id, data.comment)
    return DetailResponse(
        detail="Subscription resumed successfully",
        code="SUBSCRIPTION_RESUMED"
    )


@router.post("/{subscription_id}/cancel", response_model=DetailResponse)
async def cancel_subscription(
        subscription_id: UUID,
        data: SubscriptionCancel,
        session: AsyncSession = Depends(get_session)
):
    """Cancel a subscription"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(subscription_id)

    await subscription_service.cancel_subscription(subscription_id, data.reason, data.immediate)
    return DetailResponse(
        detail="Subscription cancelled successfully",
        code="SUBSCRIPTION_CANCELLED"
    )


@router.get("/{subscription_id}/history", response_model=list[SubscriptionHistoryResponse])
async def get_subscription_history(
        subscription_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """Get subscription history"""
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_subscription(subscription_id)

    return await subscription_service.get_subscription_history(subscription_id)


# Admin endpoints
@router.get("/admin/all", response_model=list[SubscriptionResponse])
async def list_all_subscriptions(
        session: AsyncSession = Depends(get_session)
):
    """List all subscriptions (admin only)"""
    subscription_service = SubscriptionService(session)
    return await subscription_service.get_all_subscription()


@router.get("/admin/user/{user_id}", response_model=list[SubscriptionResponse])
async def get_user_subscriptions(
        user_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """Get all subscriptions for a specific user (admin only)"""
    subscription_service = SubscriptionService(session)
    return await subscription_service.get_all_subscription({"user_id": user_id})


@router.get("/admin/due", response_model=list[SubscriptionResponse])
async def get_user_subscriptions(
        session: AsyncSession = Depends(get_session)
):
    """Get all subscriptions with today's payment date (admin only)"""
    subscription_service = SubscriptionService(session)
    return await subscription_service.get_all_subscription({"end_date": datetime.date.today()})

@router.get("/{subscription_id}/pay", response_model=SubscriptionResponse)
async def pay_for_subscription(
        subscription_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """Create a payment for the subscription with given id"""
    subscription_service = SubscriptionService(session)

    subscription = await subscription_service.get_subscription(subscription_id)

    # Подписываем через billing.src.api.v1.billing.subscribe

    async with aiohttp.ClientSession() as session:
        try:
            params = {"tariff_id": subscription.plan_id}
            async with session.post(url=f"{settings.base_url}billing/subscribe",
                    data=params,
                    timeout=30
            ) as response:
                if response.status in (200, 201):
                    return await response.json()
                logger.error(f"Failed to subscribe, status: {response.status}")
                return []
        except Exception as e:
            logger.error(f"Error during subscription process: {e}")
            return []
