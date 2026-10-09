
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.game import Game
    from app.models.rental import Rental
    from app.models.user import User


class Listing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    condition: str
    availability: bool = True
    price: float
    game: "Game" = Relationship(back_populates="listings")
    owner: "User" = Relationship(
        back_populates="listings",
        sa_relationship_kwargs={"foreign_keys": "Listing.owner_id"},
    )
    rentals: list["Rental"] = Relationship(back_populates="listing")
