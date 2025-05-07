from pymongo import MongoClient
from datetime import datetime

class AttendanceDetailDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="htnhung", collection_name="attendance_detail"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _generate_attendance_detail_id(self):
        last_attendance = self.collection.find_one(sort=[("attendance_detail_id", -1)])
        if last_attendance and "attendance_detail_id" in last_attendance:
            return last_attendance["attendance_detail_id"] + 1
        return 1

    def add_attendance_detail(self, attendances_id, time, image_url):
        attendance_detail_id = self._generate_attendance_detail_id()
        now = datetime.now()
        attendance_data = {
            "attendance_detail_id": attendance_detail_id,
            "attendances_id": attendances_id,
            "time": time,
            "image_url": image_url,
        }
        result = self.collection.insert_one(attendance_data)
        return str(result.inserted_id), attendance_detail_id

    def delete_attendance(self, attendance_detail_id: int):
        result = self.collection.delete_one({"attendance_detail_id": attendance_detail_id})
        return result.deleted_count

    def get_attendance(self, attendance_detail_id: int):
        attendance = self.collection.find_one({"attendance_detail_id": attendance_detail_id})
        return attendance

    def list_attendances(self):
        return list(self.collection.find())
