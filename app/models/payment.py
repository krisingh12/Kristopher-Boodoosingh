from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.rental import Rental
    from app.models.user import User


class Payment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="user.id", index=True)
    payment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    Amount: float
    RentalId: int | None = Field(default=None, foreign_key="rental.id")
    customer: "User" = Relationship(
        back_populates="payments",
        sa_relationship_kwargs={"foreign_keys": "Payment.customer_id"},
    )
    rental: "Rental" = Relationship(
        back_populates="payments",
        sa_relationship_kwargs={"foreign_keys": "Payment.RentalId"},
    )


RentalPayment = Payment
