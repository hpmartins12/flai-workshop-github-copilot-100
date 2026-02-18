"""
Tests for the Mergington High School API
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict to its original state before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict():
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)


def test_get_activities_contains_expected_keys():
    response = client.get("/activities")
    data = response.json()
    expected = {"Soccer Team", "Swimming Club", "Art Club", "Theater Group",
                "Debate Team", "Science Club", "Chess Club", "Programming Class", "Gym Class"}
    assert expected.issubset(data.keys())


def test_activity_has_required_fields():
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up newstudent@mergington.edu for Chess Club"
    }


def test_signup_adds_participant():
    client.post("/activities/Chess Club/signup", params={"email": "new@mergington.edu"})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert "new@mergington.edu" in participants


def test_signup_duplicate_returns_400():
    # michael@mergington.edu is already in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "test@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }


def test_unregister_removes_participant():
    client.delete("/activities/Chess Club/unregister", params={"email": "michael@mergington.edu"})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert "michael@mergington.edu" not in participants


def test_unregister_not_enrolled_returns_400():
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "nobody@mergington.edu"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Unknown Activity/unregister",
        params={"email": "test@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
