from datetime import datetime
from enum import Enum

from pydantic import EmailStr
from pydantic import Field as PydanticField
from sqlmodel import SQLModel


class Platform(str, Enum):
    NSW = "NSW"
    PS5 = "PS5"
    XBOX = "XBOX"
    PC = "PC"


class SignupRequest(SQLModel):
    username: str = PydanticField(min_length=1, max_length=100)
    email: EmailStr
    password: str = PydanticField(min_length=1)


class UserPublic(SQLModel):
    id: int
    username: str
    email: EmailStr


class LoginRequest(SQLModel):
    username: str
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


class ListingCreate(SQLModel):
    game_id: int = PydanticField(gt=0)
    condition: str = PydanticField(min_length=1, max_length=100)
    price: float = PydanticField(gt=0)


class ListingRead(SQLModel):
    id: int
    game_id: int
    owner_id: int
    condition: str
    availability: bool
    price: float


class GameCreate(SQLModel):
    title: str = PydanticField(min_length=1, max_length=200)
    rating: str
    platform: Platform
    boxart: str
    genre: str


class GameRead(SQLModel):
    id: int
    title: str
    rating: str
    platform: Platform
    boxart: str
    genre: str


class PaymentCreate(SQLModel):
    amount: float = PydanticField(gt=0)
    customer_id: int = PydanticField(gt=0)


class PaymentCreated(SQLModel):
    payment_id: int


class RentalCreate(SQLModel):
    listing_id: int = PydanticField(gt=0)
    customer_id: int = PydanticField(gt=0)


class RentalRead(SQLModel):
    id: int
    listing_id: int
    renter_id: int
    rentalDate: datetime
    returnDate: datetime | None


class RentalReturn(SQLModel):
    payment_id: int = PydanticField(gt=0)


class PaymentRead(SQLModel):
    id: int
    customer_id: int
    payment_date: datetime
    Amount: float
    RentalId: int | None
