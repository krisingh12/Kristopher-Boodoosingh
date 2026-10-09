"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.customer import Customer
from app.models.game import Game
from app.models.listing import Listing
from app.models.payment import Payment, RentalPayment
from app.models.rental import Rental
from app.models.staff import Staff
from app.models.user import User

__all__ = [
    "Customer",
    "Game",
    "Listing",
    "Payment",
    "Rental",
    "RentalPayment",
    "Staff",
    "User",
]
