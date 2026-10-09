
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.listing import Listing


class Game(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    rating: str
    platform: str = Field(index=True)
    boxart: str
    genre: str
    listings: list["Listing"] = Relationship(back_populates="game")
