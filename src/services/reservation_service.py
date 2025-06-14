from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.models.showtime_model import Showtime
from src.models.seat_model import Seat
from src.models.reservation_model import Reservation
from src.models.user_model import User
from src.schema.requests.reservation_request import ReservationCreateRequest
from src.schema.responses.reservation_response import ReservationResponse
from src.utils.logger import setup_logger
from src.config.config import get_settings

_SETTINGS = get_settings()
logger = setup_logger(__name__, level=_SETTINGS.log_level)

class ReservationService:
    async def create_reservation(
        self,
        session: AsyncSession,
        user: User,
        data: ReservationCreateRequest,
    ) -> ReservationResponse:
        # Verify showtime exists and is in the future
        result = await session.execute(
            select(Showtime).where(Showtime.id == data.showtime_id)
        )
        showtime = result.scalar_one_or_none()
        if not showtime:
            logger.warning(f"❌ Showtime not found: {data.showtime_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Showtime not found."
            )

        if showtime.show_datetime <= datetime.now():
            logger.warning("❌ Attempt to reserve past showtime")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reserve seats for past showtimes."
            )

        # Verify seat belongs to showtime
        result = await session.execute(
            select(Seat).where(
                Seat.id == data.seat_id,
                Seat.showtime_id == showtime.id
            )
        )
        seat = result.scalar_one_or_none()
        if not seat:
            logger.warning(
                f"❌ Seat {data.seat_id} not found for showtime {data.showtime_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found for this showtime."
            )

        if seat.is_reserved:
            logger.warning(
                f"❌ Seat {seat.id} already reserved for showtime {showtime.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seat is already reserved."
            )

        reservation = Reservation(
            user_id=user.id,
            showtime_id=showtime.id,
            seat_id=seat.id
        )
        seat.is_reserved = True
        session.add(reservation)
        await session.commit()
        await session.refresh(reservation)

        response = ReservationResponse(
            id=reservation.id,
            showtime_id=showtime.id,
            show_datetime=showtime.show_datetime,
            movie_title=showtime.movie.title,
            seat_id=seat.id,
            seat_number=seat.seat_number,
        )
        logger.info(
            f"✅ Reservation {reservation.id} created by user {user.email} for seat {seat.seat_number}"
        )
        return response

    async def get_user_reservations(
        self,
        session: AsyncSession,
        user: User,
    ) -> list[ReservationResponse]:
        stmt = (
            select(Reservation)
            .options(
                joinedload(Reservation.showtime).joinedload(Showtime.movie),
                joinedload(Reservation.seat)
            )
            .where(Reservation.user_id == user.id)
            .where(Showtime.show_datetime >= datetime.now())
        )
        result = await session.execute(stmt)
        reservations = result.scalars().all()

        responses = [
            ReservationResponse(
                id=r.id,
                showtime_id=r.showtime.id,
                show_datetime=r.showtime.show_datetime,
                movie_title=r.showtime.movie.title,
                seat_id=r.seat.id,
                seat_number=r.seat.seat_number,
            )
            for r in reservations
        ]
        logger.info(
            f"📄 Returned {len(responses)} reservations for user {user.email}"
        )
        return responses

    async def cancel_reservation(
        self,
        session: AsyncSession,
        user: User,
        reservation_id: int,
    ) -> None:
        stmt = (
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .options(
                joinedload(Reservation.showtime),
                joinedload(Reservation.seat)
            )
        )
        result = await session.execute(stmt)
        reservation = result.scalar_one_or_none()
        if not reservation or reservation.user_id != user.id:
            logger.warning(
                f"❌ Reservation {reservation_id} not found for user {user.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found."
            )

        if reservation.showtime.show_datetime <= datetime.now():
            logger.warning(
                f"❌ Cannot cancel past reservation {reservation_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel past reservations."
            )

        reservation.seat.is_reserved = False
        await session.delete(reservation)
        await session.commit()
        logger.info(f"🗑️ Reservation {reservation_id} cancelled by {user.email}")
