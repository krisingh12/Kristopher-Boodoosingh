from datetime import datetime, timezone

from app.models.game import Game
from app.models.listing import Listing
from app.models.payment import Payment
from app.models.rental import Rental
from app.models.user import User, UserBase


class Staff(UserBase):
    """Staff data model with staff-managed operations."""

    id: int | None = None

    @staticmethod
    def list_game(session, game: Game) -> Game:
        session.add(game)
        session.commit()
        session.refresh(game)
        return game

    @staticmethod
    def confirm_rental(
        session,
        listing: Listing,
        customer: User,
    ) -> Rental:
        rental = Rental(listing_id=listing.id, renter_id=customer.id)
        listing.availability = False
        session.add(listing)
        session.add(rental)
        session.commit()
        session.refresh(rental)
        return rental

    @staticmethod
    def confirm_return(
        session,
        rental: Rental,
        payment: Payment,
        listing: Listing,
    ) -> Rental:
        payment.RentalId = rental.id
        rental.returnDate = datetime.now(timezone.utc)
        listing.availability = True
        session.add(payment)
        session.add(listing)
        session.add(rental)
        session.commit()
        session.refresh(rental)
        return rental
