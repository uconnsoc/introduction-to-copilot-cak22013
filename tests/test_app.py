"""
Test suite for the Mergington High School Activities API.
Uses the Arrange-Act-Assert (AAA) pattern for clear test structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities state before each test"""
    # Store original state
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        }
    }
    
    # Reset before test
    activities.clear()
    activities.update(original)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities_returns_200(self, client, reset_activities):
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Basketball Team"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        assert all(activity in response.json() for activity in expected_activities)
    
    def test_get_activities_returns_activity_details(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        assert activity_name in activities_data
        assert all(field in activities_data[activity_name] for field in required_fields)
    
    def test_get_activities_includes_current_participants(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        chess_club = response.json()[activity_name]
        
        # Assert
        assert all(participant in chess_club["participants"] for participant in expected_participants)
    
    def test_get_activities_shows_empty_participant_list(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        
        # Act
        response = client.get("/activities")
        basketball = response.json()[activity_name]
        
        # Assert
        assert basketball["participants"] == []


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_returns_200(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        
        # Assert
        assert email in response.json()[activity_name]["participants"]
    
    def test_signup_increases_participant_count(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"
        
        # Act
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        
        # Assert
        assert count_after == count_before + 1
    
    def test_signup_to_nonexistent_activity_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_twice_returns_400(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_returns_confirmation_message(self, client, reset_activities):
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert email in response.json()["message"]
        assert activity_name in response.json()["message"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful_returns_200(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant_from_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        response = client.get("/activities")
        
        # Assert
        assert email not in response.json()[activity_name]["participants"]
    
    def test_unregister_decreases_participant_count(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        
        # Assert
        assert count_after == count_before - 1
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client, reset_activities):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_signed_up_returns_400(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_returns_confirmation_message(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert email in response.json()["message"]
        assert activity_name in response.json()["message"]
    
    def test_unregister_same_user_twice_returns_400(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - First unregister should succeed
        response_first = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Act - Second unregister should fail
        response_second = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response_first.status_code == 200
        assert response_second.status_code == 400
        assert "not signed up" in response_second.json()["detail"].lower()


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_unregister_workflow(self, client, reset_activities):
        # Arrange
        activity_name = "Basketball Team"
        email = "athlete@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert signup succeeded
        assert signup_response.status_code == 200
        
        # Act - Verify signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert unregister succeeded
        assert unregister_response.status_code == 200
        
        # Act - Verify unregistered
        final_response = client.get("/activities")
        assert email not in final_response.json()[activity_name]["participants"]
    
    def test_multiple_signup_and_unregister_operations(self, client, reset_activities):
        # Arrange
        activity_name = "Programming Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act - Sign up multiple students
        for email in emails:
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert all signed up
        response = client.get("/activities")
        for email in emails:
            assert email in response.json()[activity_name]["participants"]
        
        # Act - Unregister one student
        client.delete(f"/activities/{activity_name}/unregister?email={emails[0]}")
        
        # Assert one unregistered, others still signed up
        response = client.get("/activities")
        assert emails[0] not in response.json()[activity_name]["participants"]
        assert emails[1] in response.json()[activity_name]["participants"]
        assert emails[2] in response.json()[activity_name]["participants"]
