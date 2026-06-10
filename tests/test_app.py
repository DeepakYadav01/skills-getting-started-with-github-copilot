"""Tests for the Mergington High School Activities API using AAA (Arrange-Act-Assert) pattern"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestRoot:
    """Tests for root endpoint"""

    def test_root_redirect(self):
        """Root should redirect to static index.html"""
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_location


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_dict(self):
        """Should return all activities as a dict"""
        # Arrange
        expected_status = 200
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_has_required_fields(self):
        """Each activity should have required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_contains_chess_club(self):
        """Should contain Chess Club activity"""
        # Arrange
        expected_activity = "Chess Club"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert expected_activity in data


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Should successfully sign up a student"""
        # Arrange
        activity = "Chess Club"
        email = "signup_success@mergington.edu"
        expected_status = 200
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert "message" in data
        assert email in data["message"]

    def test_signup_duplicate_fails(self):
        """Should not allow duplicate signup"""
        # Arrange
        activity = "Chess Club"
        email = "duplicate@mergington.edu"
        expected_fail_status = 400
        
        # Act - First signup succeeds
        first_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Act - Second signup fails
        second_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        second_data = second_response.json()
        
        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == expected_fail_status
        assert "already signed up" in second_data["detail"].lower()

    def test_signup_nonexistent_activity(self):
        """Should return 404 for non-existent activity"""
        # Arrange
        activity = "NonExistentActivity"
        email = "test@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert "not found" in data["detail"].lower()

    def test_signup_adds_to_participants(self):
        """New participant should appear in activity"""
        # Arrange
        activity = "Programming Class"
        email = "newstudent123@mergington.edu"
        
        # Act
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        # Assert
        assert signup_response.status_code == 200
        assert email in activities_data[activity]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_success(self):
        """Should successfully remove a participant"""
        # Arrange
        activity = "Gym Class"
        email = "removetest@mergington.edu"
        expected_status = 200
        
        # Act - Sign up first
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Remove participant
        response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert "removed" in data["message"].lower()

    def test_remove_nonexistent_participant(self):
        """Should return 404 when removing non-existent participant"""
        # Arrange
        activity = "Chess Club"
        email = "notexist@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert "not found" in data["detail"].lower()

    def test_remove_from_nonexistent_activity(self):
        """Should return 404 when activity doesn't exist"""
        # Arrange
        activity = "FakeActivity"
        email = "test@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == expected_status
        assert "not found" in data["detail"].lower()

    def test_remove_updates_participants_list(self):
        """Participant should no longer appear after removal"""
        # Arrange
        activity = "Art Studio"
        email = "student_removal@mergington.edu"
        
        # Act - Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert - Verify in list
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity]["participants"]
        assert email in participants_before
        
        # Act - Remove
        client.delete(f"/activities/{activity}/participants?email={email}")
        
        # Assert - Verify not in list
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity]["participants"]
        assert email not in participants_after


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_signup_with_special_characters_in_email(self):
        """Should handle emails with special characters"""
        # Arrange
        activity = "Math Olympiad"
        email = "user+test@mergington.edu"
        expected_status = 200
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status

    def test_signup_to_activity_with_spaces_in_name(self):
        """Should handle activity names with spaces"""
        # Arrange
        activity = "Programming Class"
        email = "test_spaces@mergington.edu"
        expected_status = 200
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status

    def test_activity_name_case_sensitivity(self):
        """Activity names should be case-sensitive"""
        # Arrange
        activity = "chess club"  # lowercase (should not match "Chess Club")
        email = "case_test@mergington.edu"
        expected_status = 404
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status
