
from sqlmodel import Field

from app.models.listing import Listing
from app.models.payment import Payment
from app.models.rental import Rental
from app.models.user import CustomerStatus, UserBase


class Customer(UserBase):
    """Customer data model with payment, listing, and rental records."""

    id: int | None = None
    status: CustomerStatus = CustomerStatus.Active
    payments: list[Payment] = Field(default_factory=list)
    listings: list[Listing] = Field(default_factory=list)
    rentals: list[Rental] = Field(default_factory=list)
