import pytest
import requests
import json

class TestUsersAPI:
    """Автотесты для эндпоинта users"""
    
    @pytest.fixture
    def valid_user_data(self):
        return {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30
        }
    
    @pytest.fixture
    def invalid_user_data(self):
        return {
            "name": "",
            "email": "invalid-email",
            "age": -5
        }
    
    
    @pytest.mark.parametrize("user_data, expected_status", [
        ({"name": "Alice", "email": "alice@example.com", "age": 0}, 201),
        ({"name": "Bob", "email": "bob@example.com", "age": 150}, 201),
        ({"name": "Charlie", "email": "charlie@example.com", "age": 25}, 201),
        ({"name": "A", "email": "a@example.com", "age": 20}, 201),
        ({"name": "X" * 100, "email": "long@example.com", "age": 20}, 201),
    ])
    def test_create_user_success(self, api_base_url, db_cursor, cleanup_user, 
                                  user_data, expected_status):
        """
        Позитивный тест создания пользователя с проверкой в БД
        Используются техники: граничные значения, классы эквивалентности
        """
        response = requests.post(
            f"{api_base_url}/api/users",
            json=user_data
        )
        
        assert response.status_code == expected_status
        
        response_json = response.json()
        assert "id" in response_json
        assert response_json["name"] == user_data["name"]
        assert response_json["email"] == user_data["email"]
        assert response_json["age"] == user_data["age"]
        assert "created_at" in response_json
        
        user_id = response_json["id"]
        cleanup_user(user_id) 
        
        db_cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        db_user = db_cursor.fetchone()
        
        assert db_user is not None
        assert db_user["name"] == user_data["name"]
        assert db_user["email"] == user_data["email"]
        assert db_user["age"] == user_data["age"]
    
    def test_get_all_users(self, api_base_url, db_cursor, cleanup_user, valid_user_data):
        """Позитивный тест получения всех пользователей"""
        create_response = requests.post(
            f"{api_base_url}/api/users",
            json=valid_user_data
        )
        assert create_response.status_code == 201
        created_user = create_response.json()
        cleanup_user(created_user["id"])
        
        response = requests.get(f"{api_base_url}/api/users")
        
        assert response.status_code == 200
        
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1
        
        found = any(user["id"] == created_user["id"] for user in users)
        assert found is True
        
        db_cursor.execute("SELECT COUNT(*) FROM users")
        db_count = db_cursor.fetchone()["count"]
        assert len(users) == db_count
    
    @pytest.mark.parametrize("user_data, update_data", [
        (
            {"name": "Original", "email": "original@example.com", "age": 20},
            {"name": "Updated", "email": "updated@example.com", "age": 25}
        ),
        (
            {"name": "Original", "email": "original2@example.com", "age": 20},
            {"name": "New Name"}
        ),
        (
            {"name": "Age Test", "email": "age@example.com", "age": 10},
            {"age": 150}
        ),
    ])
    def test_update_user_success(self, api_base_url, db_cursor, cleanup_user,
                                  user_data, update_data):
        """Позитивный тест обновления пользователя с проверкой в БД"""
        create_response = requests.post(
            f"{api_base_url}/api/users",
            json=user_data
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        cleanup_user(user_id)
        
        response = requests.put(
            f"{api_base_url}/api/users/{user_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        response_json = response.json()
        assert response_json["id"] == user_id
        
        for key, value in update_data.items():
            assert response_json[key] == value
        
        db_cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        db_user = db_cursor.fetchone()
        
        assert db_user is not None
        for key, value in update_data.items():
            assert db_user[key] == value
        
        for key in user_data:
            if key not in update_data:
                assert db_user[key] == user_data[key]
    
    def test_delete_user_success(self, api_base_url, db_cursor, valid_user_data):
        """Позитивный тест удаления пользователя с проверкой в БД"""
        create_response = requests.post(
            f"{api_base_url}/api/users",
            json=valid_user_data
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        db_cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        assert db_cursor.fetchone() is not None
        
        response = requests.delete(f"{api_base_url}/api/users/{user_id}")
        
        assert response.status_code == 204
        assert response.text == ""  # Нет тела ответа
        
        db_cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        assert db_cursor.fetchone() is None
    
    def test_get_user_by_id_success(self, api_base_url, db_cursor, cleanup_user, valid_user_data):
        """Позитивный тест получения пользователя по ID"""
        create_response = requests.post(
            f"{api_base_url}/api/users",
            json=valid_user_data
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        cleanup_user(user_id)
        
        response = requests.get(f"{api_base_url}/api/users/{user_id}")
        
        assert response.status_code == 200
        
        response_json = response.json()
        assert response_json["id"] == user_id
        assert response_json["name"] == valid_user_data["name"]
        assert response_json["email"] == valid_user_data["email"]
        assert response_json["age"] == valid_user_data["age"]
        
        db_cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        db_user = db_cursor.fetchone()
        assert db_user["name"] == response_json["name"]
        assert db_user["email"] == response_json["email"]
    
    
    @pytest.mark.parametrize("invalid_data, expected_status, expected_error", [
        ({"name": "", "email": "test@example.com", "age": 20}, 400, "Name is required"),
        ({"name": "Test", "email": "invalid-email", "age": 20}, 400, "Invalid email format"),
        ({"name": "Test", "email": "test@example.com", "age": -1}, 400, "Age must be between 0 and 150"),
        ({"name": "Test", "email": "test@example.com", "age": 151}, 400, "Age must be between 0 and 150"),
        ({"name": "Test", "email": "test@example.com"}, 400, "Age is required"),
        ({"name": "X" * 101, "email": "test@example.com", "age": 20}, 400, "Name must be less than 100 characters"),
    ])
    def test_create_user_invalid_data(self, api_base_url, invalid_data, 
                                       expected_status, expected_error):
        """Негативный тест создания пользователя с невалидными данными"""
        response = requests.post(
            f"{api_base_url}/api/users",
            json=invalid_data
        )
        
        assert response.status_code == expected_status
        
        response_json = response.json()
        assert "error" in response_json
        assert expected_error in response_json["error"]
    
    def test_get_nonexistent_user(self, api_base_url):
        """Негативный тест получения несуществующего пользователя"""
        response = requests.get(f"{api_base_url}/api/users/99999")
        
        assert response.status_code == 404
        response_json = response.json()
        assert "error" in response_json
        assert "User not found" in response_json["error"]
    
    def test_update_nonexistent_user(self, api_base_url):
        """Негативный тест обновления несуществующего пользователя"""
        response = requests.put(
            f"{api_base_url}/api/users/99999",
            json={"name": "Updated"}
        )
        
        assert response.status_code == 404
        response_json = response.json()
        assert "error" in response_json
        assert "User not found" in response_json["error"]
    
    def test_delete_nonexistent_user(self, api_base_url):
        """Негативный тест удаления несуществующего пользователя"""
        response = requests.delete(f"{api_base_url}/api/users/99999")
        
        assert response.status_code == 404
        response_json = response.json()
        assert "error" in response_json
        assert "User not found" in response_json["error"]
    
    def test_create_user_duplicate_email(self, api_base_url, db_cursor, cleanup_user, valid_user_data):
        """Негативный тест создания пользователя с дублирующимся email"""
        response1 = requests.post(
            f"{api_base_url}/api/users",
            json=valid_user_data
        )
        assert response1.status_code == 201
        user_id = response1.json()["id"]
        cleanup_user(user_id)
        
        response2 = requests.post(
            f"{api_base_url}/api/users",
            json=valid_user_data
        )
        
        assert response2.status_code == 409
        response_json = response2.json()
        assert "error" in response_json
        assert "Email already exists" in response_json["error"]
