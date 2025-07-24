from fastapi.testclient import TestClient
from app import app, init_db, create_user
import unittest
from PIL import Image
import io
import os
import base64

client = TestClient(app)

class Test_Count(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists("predictions.db"):
            os.remove("predictions.db")
        init_db()
        create_user("admin", "1234")
        os.makedirs("uploads/original", exist_ok=True)
        os.makedirs("uploads/predicted", exist_ok=True)

    def setUp(self):
        self.auth = ("admin", "1234")
        # Create an in-memory image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        self.image_bytes = buf

    def test_prediction_count_after_prediction(self):
        client.post(
            "/predict",
            files={"file": ("test.jpg", self.image_bytes, "image/jpeg")}
        )
        response = client.get("/prediction/count", auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
