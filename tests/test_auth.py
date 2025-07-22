import unittest
import sqlite3
from app import authenticate, DB_PATH, init_db
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

class TestAuthentication(unittest.TestCase):

    def setUp(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DROP TABLE IF EXISTS users")
            conn.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            """)
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                         ("admin", "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"))  # "1234" in SHA-256

    def test_authenticate_success(self):
        credentials = HTTPBasicCredentials(username="admin", password="1234")
        result = authenticate(credentials)
        self.assertEqual(result["username"], "admin")

    def test_authenticate_wrong_password(self):
        credentials = HTTPBasicCredentials(username="admin", password="wrong")
        with self.assertRaises(HTTPException) as context:
            authenticate(credentials)
        self.assertEqual(context.exception.status_code, 401)

    def test_authenticate_nonexistent_user(self):
        credentials = HTTPBasicCredentials(username="nouser", password="any")
        with self.assertRaises(HTTPException) as context:
            authenticate(credentials)
        self.assertEqual(context.exception.status_code, 401)

if __name__ == '__main__':
    unittest.main()
