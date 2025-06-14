from pydantic import BaseModel

class ReservationCreateRequest(BaseModel):
    showtime_id: int
    seat_id: int
