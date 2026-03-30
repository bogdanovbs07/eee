import pytest
import psycopg2
from psycopg2 import extras
import requests

def pytest_addoption(parser):
    """Хук для добавления командной строки для строки подключения к БД"""
    parser.addoption(
        "--db-url",
        action="store",
        default="postgresql://postgres:password@localhost:5432/test_db",
        help="Database connection URL"
    )
    parser.addoption(
        "--api-base-url",
        action="store",
        default="http://localhost:5000",
        help="API base URL"
    )

@pytest.fixture(scope="session")
def db_connection(request):
    """Фикстура подключения к базе данных"""
    db_url = request.config.getoption("--db-url")
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    
    yield conn
    
    conn.close()

@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """Фикстура для получения курсора БД"""
    cursor = db_connection.cursor(cursor_factory=extras.RealDictCursor)
    yield cursor
    cursor.close()

@pytest.fixture(scope="session")
def api_base_url(request):
    """Фикстура для получения базового URL API"""
    return request.config.getoption("--api-base-url")

@pytest.fixture(scope="function")
def cleanup_user(db_connection):
    """Фикстура для очистки тестовых данных"""
    created_users = []
    
    def _add_user(user_id):
        created_users.append(user_id)
    
    yield _add_user
    
    if created_users:
        cursor = db_connection.cursor()
        cursor.execute(
            "DELETE FROM users WHERE id = ANY(%s)",
            (created_users,)
        )
        db_connection.commit()
        cursor.close()

@pytest.fixture(scope="session", autouse=True)
def setup_database(db_connection):
    """Фикстура для создания тестовой таблицы"""
    cursor = db_connection.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            age INTEGER CHECK (age >= 0 AND age <= 150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db_connection.commit()
    cursor.close()
    
    yield
    
