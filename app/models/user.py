from enum import Enum
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.payment import Payment
    from app.models.rental import Rental


class CustomerStatus(str, Enum):
    Active = "Active"
    InActive = "InActive"


class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role:str = ""

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = Field(default=CustomerStatus.Active.value)
    payments: list["Payment"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"foreign_keys": "Payment.customer_id"},
    )
    listings: list["Listing"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "Listing.owner_id"},
    )
    rentals: list["Rental"] = Relationship(
        back_populates="renter",
        sa_relationship_kwargs={"foreign_keys": "Rental.renter_id"},
    )