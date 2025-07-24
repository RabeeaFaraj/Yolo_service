import unittest
import sqlite3
import os
from app import save_detection_object, DB_PATH

class TestSaveDetectionObject(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE detection_objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_uid TEXT,
                    label TEXT,
                    score REAL,
                    box TEXT
                )
            """)

    def test_save_detection_object(self):
        uid = "test-uid"
        label = "cat"
        score = 0.95
        box = [100, 100, 200, 200]

        save_detection_object(uid, label, score, box)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT prediction_uid, label, score, box FROM detection_objects")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], uid)
            self.assertEqual(row[1], label)
            self.assertAlmostEqual(row[2], score)
            self.assertEqual(row[3], str(box))
