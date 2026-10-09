from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.payment import Payment
    from app.models.user import User


class Rental(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id", index=True)
    renter_id: int = Field(foreign_key="user.id", index=True)
    rentalDate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    returnDate: datetime | None = None
    listing: "Listing" = Relationship(back_populates="rentals")
    renter: "User" = Relationship(
        back_populates="rentals",
        sa_relationship_kwargs={"foreign_keys": "Rental.renter_id"},
    )
    payments: list["Payment"] = Relationship(
        back_populates="rental",
        sa_relationship_kwargs={"foreign_keys": "Payment.RentalId"},
    )
