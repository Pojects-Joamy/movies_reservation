from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.config.db_config import get_db
from src.models.user_model import User
from src.security.dependencies import get_current_user
from src.services.reservation_service import ReservationService
from src.schema.requests.reservation_request import ReservationCreateRequest
from src.schema.responses.reservation_response import ReservationResponse
from src.utils.logger import setup_logger
from src.config.config import get_settings

_SETTINGS = get_settings()
logger = setup_logger(__name__, level=_SETTINGS.log_level)

router = APIRouter(prefix="/reservations")
reservation_service = ReservationService()

@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reservations"]
)
async def create_reservation(
    reservation: ReservationCreateRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    logger.info(
        f"🎟️ User {user.email} reserving seat {reservation.seat_id} for showtime {reservation.showtime_id}"
    )
    return await reservation_service.create_reservation(session, user, reservation)

@router.get(
    "/",
    response_model=List[ReservationResponse],
    status_code=200,
    tags=["Reservations"]
)
async def list_my_reservations(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    logger.info(f"📄 Listing reservations for user {user.email}")
    return await reservation_service.get_user_reservations(session, user)

@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Reservations"]
)
async def cancel_reservation(
    reservation_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    logger.info(f"❌ User {user.email} cancel reservation {reservation_id}")
    await reservation_service.cancel_reservation(session, user, reservation_id)
    return
