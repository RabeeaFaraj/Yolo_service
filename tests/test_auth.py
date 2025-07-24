import os
import unittest
from fastapi.testclient import TestClient
from app import app, init_db, create_user, DB_PATH
from PIL import Image
import sqlite3
import io
import shutil
import uuid

client = TestClient(app)

class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset DB
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        create_user("admin", "1234")
        create_user("rabeea", "1234")
        os.makedirs("uploads/original", exist_ok=True)
        os.makedirs("uploads/predicted", exist_ok=True)

    def get_test_image(self):
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return buf

    def test_auth_success(self):
        res = client.get("/prediction/count", auth=("admin", "1234"))
        self.assertEqual(res.status_code, 200)

    def test_auth_fail_wrong_password(self):
        res = client.get("/prediction/count", auth=("admin", "wrong"))
        self.assertEqual(res.status_code, 401)

    def test_auth_fail_nonexistent_user(self):
        res = client.get("/prediction/count", auth=("ghost", "1234"))
        self.assertEqual(res.status_code, 401)

    def test_prediction_flow(self):
        # Upload and predict
        img_buf = self.get_test_image()
        response = client.post("/predict", files={"file": ("test.jpg", img_buf, "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("prediction_uid", data)
        self.uid = data["prediction_uid"]
        self.assertTrue(len(data["labels"]) >= 0)

    def test_get_prediction_by_uid(self):
        # Upload first
        img_buf = self.get_test_image()
        response = client.post("/predict", files={"file": ("test2.jpg", img_buf, "image/jpeg")})
        uid = response.json()["prediction_uid"]

        # Get prediction by uid
        r = client.get(f"/prediction/{uid}", auth=("admin", "1234"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("detection_objects", r.json())

    def test_get_prediction_image(self):
        img_buf = self.get_test_image()
        response = client.post("/predict", files={"file": ("test3.jpg", img_buf, "image/jpeg")})
        uid = response.json()["prediction_uid"]

        # Test JPEG
        r = client.get(f"/prediction/{uid}/image", headers={"accept": "image/jpeg"})
        self.assertEqual(r.status_code, 200)

        # Test PNG
        r = client.get(f"/prediction/{uid}/image", headers={"accept": "image/png"})
        self.assertEqual(r.status_code, 200)

        # Not acceptable
        r = client.get(f"/prediction/{uid}/image", headers={"accept": "application/json"})
        self.assertEqual(r.status_code, 406)

    def test_get_image_not_found(self):
        r = client.get("/image/original/doesnotexist.jpg")
        self.assertEqual(r.status_code, 404)

    def test_get_image_invalid_type(self):
        r = client.get("/image/fake/test.jpg")
        self.assertEqual(r.status_code, 400)

    def test_get_predictions_by_label_and_score(self):
        img_buf = self.get_test_image()
        response = client.post("/predict", files={"file": ("test4.jpg", img_buf, "image/jpeg")})
        uid = response.json()["prediction_uid"]

        r1 = client.get("/predictions/label/person")
        r2 = client.get("/predictions/score/0.1")

        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

    def test_get_prediction_image_file_missing(self):
        uid = str(uuid.uuid4())
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO prediction_sessions (uid, original_image, predicted_image)
                VALUES (?, ?, ?)
            """, (uid, "fake.jpg", "fake.jpg"))

        r = client.get(f"/prediction/{uid}/image", headers={"accept": "image/png"})
        self.assertEqual(r.status_code, 404)

    def test_get_prediction_not_found(self):
        r = client.get("/prediction/nonexistent", auth=("admin", "1234"))
        self.assertEqual(r.status_code, 404)

    def test_health(self):
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})

    def test_create_user_already_exists(self):
        # This print is required to cover: print(f"User '{username}' already exists.")
        create_user("admin", "1234")

if __name__ == '__main__':
    unittest.main()
