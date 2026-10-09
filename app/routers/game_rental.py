from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.config import get_settings
from app.dependencies import SessionDep
from app.models import Game, Listing, Payment, Rental, Staff, User
from app.repositories.user import UserRepository
from app.schemas.game_rental import (
    GameCreate,
    GameRead,
    ListingCreate,
    ListingRead,
    LoginRequest,
    PaymentCreate,
    PaymentCreated,
    Platform,
    RentalCreate,
    RentalRead,
    RentalReturn,
    SignupRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService
from app.utilities.security import encrypt_password

router = APIRouter(tags=["Game Rental API"])


def get_api_user(
    db: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(
            token,
            get_settings().secret_key,
            algorithms=[get_settings().jwt_algorithm],
        )
        subject = payload.get("sub")
        user_id = int(subject)
    except (InvalidTokenError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


ApiUserDep = Annotated[User, Depends(get_api_user)]


def require_customer(user: ApiUserDep) -> User:
    if user.role not in {"customer", "regular_user"}:
        raise HTTPException(status_code=403, detail="Customer access required")
    if user.status != "Active":
        raise HTTPException(status_code=403, detail="Customer account is inactive")
    return user


def require_staff(user: ApiUserDep) -> User:
    if user.role not in {"staff", "admin"}:
        raise HTTPException(status_code=403, detail="Staff access required")
    return user


CustomerDep = Annotated[User, Depends(require_customer)]
StaffDep = Annotated[User, Depends(require_staff)]


@router.post(
    "/signup",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def signup(body: SignupRequest, db: SessionDep):
    existing = db.exec(
        select(User).where(
            (User.username == body.username) | (User.email == body.email)
        )
    ).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=body.username,
        email=body.email,
        password=encrypt_password(body.password),
        role="regular_user",
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists",
        ) from None
    return user


@router.post("/auth", response_model=TokenResponse)
def authenticate(body: LoginRequest, db: SessionDep):
    token = AuthService(UserRepository(db)).authenticate_user(
        body.username,
        body.password,
    )
    if token is None:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )
    return TokenResponse(access_token=token)


@router.post(
    "/listings",
    response_model=ListingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_listing(
    body: ListingCreate,
    db: SessionDep,
    customer: CustomerDep,
):
    if db.get(Game, body.game_id) is None:
        raise HTTPException(status_code=404, detail="Game not found")
    listing = Listing(
        game_id=body.game_id,
        owner_id=customer.id,
        condition=body.condition,
        price=body.price,
        availability=True,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/listings", response_model=list[ListingRead])
def get_listings(
    db: SessionDep,
    platform: Platform | None = None,
):
    query = select(Listing).where(Listing.availability.is_(True))
    if platform is not None:
        query = query.join(Game, Listing.game_id == Game.id).where(
            Game.platform == platform.value
        )
    return db.exec(query).all()


@router.post(
    "/payment",
    response_model=PaymentCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    body: PaymentCreate,
    db: SessionDep,
    _staff: StaffDep,
):
    customer = db.get(User, body.customer_id)
    if customer is None or customer.role not in {"customer", "regular_user"}:
        raise HTTPException(status_code=404, detail="Customer not found")
    payment = Payment(customer_id=customer.id, Amount=body.amount)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return PaymentCreated(payment_id=payment.id)


@router.post(
    "/rentals",
    response_model=RentalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_rental(
    body: RentalCreate,
    db: SessionDep,
    _staff: StaffDep,
):
    listing = db.get(Listing, body.listing_id)
    customer = db.get(User, body.customer_id)
    if listing is None or customer is None:
        raise HTTPException(status_code=404, detail="Listing or customer not found")
    if customer.role not in {"customer", "regular_user"}:
        raise HTTPException(status_code=404, detail="Listing or customer not found")
    if not listing.availability:
        raise HTTPException(status_code=404, detail="Listing is not available")

    return Staff.confirm_rental(db, listing, customer)


@router.put(
    "/rentals/{rental_id}",
    response_model=RentalRead,
    status_code=status.HTTP_201_CREATED,
)
def confirm_return(
    rental_id: int,
    body: RentalReturn,
    db: SessionDep,
    _staff: StaffDep,
):
    rental = db.get(Rental, rental_id)
    payment = db.get(Payment, body.payment_id)
    if rental is None or payment is None:
        raise HTTPException(status_code=404, detail="Rental or payment not found")
    if payment.customer_id != rental.renter_id or payment.RentalId is not None:
        raise HTTPException(status_code=404, detail="Rental or payment not found")
    listing = db.get(Listing, rental.listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Rental listing not found")
    return Staff.confirm_return(db, rental, payment, listing)


@router.post(
    "/listings/{listing_id}/sell",
    response_model=ListingRead,
)
def sell_listing(
    listing_id: int,
    db: SessionDep,
    user: ApiUserDep,
):
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can sell this listing")
    if not listing.availability:
        raise HTTPException(status_code=404, detail="Listing is not available")
    listing.availability = False
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.post(
    "/games",
    response_model=GameRead,
    status_code=status.HTTP_201_CREATED,
)
def create_game(
    body: GameCreate,
    db: SessionDep,
    _staff: StaffDep,
):
    game = Game(
        title=body.title,
        rating=body.rating,
        platform=body.platform.value,
        boxart=body.boxart,
        genre=body.genre,
    )
    return Staff.list_game(db, game)
