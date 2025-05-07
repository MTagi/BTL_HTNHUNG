from pymongo import MongoClient
from datetime import datetime

class AttendanceDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="htnhung", collection_name="attendances"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _generate_attendance_id(self):
        last_attendance = self.collection.find_one(sort=[("attendance_id", -1)])
        if last_attendance and "attendance_id" in last_attendance:
            return last_attendance["attendance_id"] + 1
        return 1

    def add_attendance(self, driver_id: int, date, checkin_time, folder_path):
        attendance_id = self._generate_attendance_id()
        attendance_data = {
            "attendance_id": attendance_id,
            "driver_id": driver_id,
            "date": date,
            "checkin_time": checkin_time,
            "checkout_time": None,
            "folder_path": folder_path
        }
        result = self.collection.insert_one(attendance_data)
        return str(result.inserted_id), attendance_id

    def update_attendance(self, attendance_id: int, driver_id: int, checkout_time: str):
        update_data = {
            "driver_id": driver_id,
            "checkout_time": checkout_time,
        }
        result = self.collection.update_one(
            {"attendance_id": attendance_id},
            {"$set": update_data}
        )
        return result.modified_count

    def delete_attendance(self, attendance_id: int):
        result = self.collection.delete_one({"attendance_id": attendance_id})
        return result.deleted_count

    def get_attendance(self, attendance_id: int):
        attendance = self.collection.find_one({"attendance_id": attendance_id})
        return attendance

    def list_attendances(self):
        return list(self.collection.find())
