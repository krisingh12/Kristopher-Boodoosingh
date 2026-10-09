import pytest
from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app
from app.models import User
from app.utilities.security import encrypt_password


@pytest.fixture
def api_client(test_session):
    def override_session():
        yield test_session

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_session, None)


def test_game_rental_lifecycle(api_client, test_session):
    staff = User(
        username="staff",
        email="staff@example.com",
        password=encrypt_password("staff-secret"),
        role="staff",
    )
    test_session.add(staff)
    test_session.commit()

    signup = api_client.post(
        "/signup",
        json={
            "username": "renter",
            "email": "renter@example.com",
            "password": "renter-secret",
        },
    )
    assert signup.status_code == 201
    customer_id = signup.json()["id"]
    duplicate_signup = api_client.post(
        "/signup",
        json={
            "username": "renter",
            "email": "another@example.com",
            "password": "renter-secret",
        },
    )
    assert duplicate_signup.status_code == 400

    login = api_client.post(
        "/auth",
        json={"username": "staff", "password": "staff-secret"},
    )
    assert login.status_code == 200
    staff_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    game_response = api_client.post(
        "/games",
        headers=staff_headers,
        json={
            "title": "Test game",
            "rating": "E",
            "platform": "PS5",
            "boxart": "https://example.com/game.png",
            "genre": "Adventure",
        },
    )
    assert game_response.status_code == 201
    game_id = game_response.json()["id"]

    customer_login = api_client.post(
        "/auth",
        json={"username": "renter", "password": "renter-secret"},
    )
    customer_headers = {
        "Authorization": f"Bearer {customer_login.json()['access_token']}"
    }
    assert api_client.post(
        "/games",
        headers=customer_headers,
        json={
            "title": "Unauthorized game",
            "rating": "E",
            "platform": "PS5",
            "boxart": "https://example.com/game.png",
            "genre": "Adventure",
        },
    ).status_code == 403
    assert api_client.post(
        "/listings",
        headers=customer_headers,
        json={"game_id": game_id + 100, "condition": "Good", "price": 12.5},
    ).status_code == 404
    listing_response = api_client.post(
        "/listings",
        headers=customer_headers,
        json={"game_id": game_id, "condition": "Good", "price": 12.5},
    )
    assert listing_response.status_code == 201
    listing_id = listing_response.json()["id"]
    assert api_client.post(
        f"/listings/{listing_id}/sell",
        headers=staff_headers,
    ).status_code == 403

    assert api_client.get("/listings?platform=PS5").json()[0]["id"] == listing_id
    assert api_client.get("/listings?platform=XBOX").json() == []

    payment_response = api_client.post(
        "/payment",
        headers=staff_headers,
        json={"amount": 12.5, "customer_id": customer_id},
    )
    assert payment_response.status_code == 201
    payment_id = payment_response.json()["payment_id"]

    rental_response = api_client.post(
        "/rentals",
        headers=staff_headers,
        json={"listing_id": listing_id, "customer_id": customer_id},
    )
    assert rental_response.status_code == 201
    rental_id = rental_response.json()["id"]
    assert api_client.get("/listings?platform=PS5").json() == []

    return_response = api_client.put(
        f"/rentals/{rental_id}",
        headers=staff_headers,
        json={"payment_id": payment_id},
    )
    assert return_response.status_code == 201
    assert api_client.put(
        "/rentals/999999",
        headers=staff_headers,
        json={"payment_id": payment_id},
    ).status_code == 404
    assert return_response.json()["returnDate"] is not None
    assert len(api_client.get("/listings?platform=PS5").json()) == 1

    sell_response = api_client.post(
        f"/listings/{listing_id}/sell",
        headers=customer_headers,
    )
    assert sell_response.status_code == 200
    assert sell_response.json()["availability"] is False
    assert api_client.get("/listings?platform=PS5").json() == []


def test_api_validation_and_authorization(api_client):
    assert api_client.post(
        "/signup",
        json={
            "username": "invalid-email",
            "email": "not-an-email",
            "password": "secret",
        },
    ).status_code == 422
    assert api_client.post(
        "/auth",
        json={"username": "unknown", "password": "incorrect"},
    ).status_code == 400
    assert api_client.post(
        "/listings",
        json={"game_id": 1, "condition": "Good", "price": 1},
    ).status_code == 401
    assert api_client.get("/listings?platform=SWITCH").status_code == 422
