from pydantic import BaseModel
from datetime import datetime

class ReservationResponse(BaseModel):
    id: int
    showtime_id: int
    show_datetime: datetime
    movie_title: str
    seat_id: int
    seat_number: str

    class Config:
        from_attributes = True
