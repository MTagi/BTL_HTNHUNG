from pymongo import MongoClient
from datetime import datetime

class DriverLocationDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="htnhung", collection_name="driver_locations"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _generate_location_id(self):
        last_location = self.collection.find_one(sort=[("location_id", -1)])
        if last_location and "location_id" in last_location:
            return last_location["location_id"] + 1
        return 1

    def add_driver_location(self, driver_id: int, vehicle_id: int, timestamp, latitude: float, longitude: float):
        location_id = self._generate_location_id()
        now = datetime.now()
        location_data = {
            "location_id": location_id,
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude
        }
        result = self.collection.insert_one(location_data)
        return str(result.inserted_id), location_id

    def update_driver_location(self, location_id: int, latitude: float, longitude: float):
        update_data = {
            "latitude": latitude,
            "longitude": longitude
        }
        result = self.collection.update_one(
            {"location_id": location_id},
            {"$set": update_data}
        )
        return result.modified_count

    def delete_driver_location(self, location_id: int):
        result = self.collection.delete_one({"location_id": location_id})
        return result.deleted_count

    def get_driver_location(self, location_id: int):
        location = self.collection.find_one({"location_id": location_id})
        return location

    def list_driver_locations(self):
        return list(self.collection.find())
    def list_locations_by_vehicle(self, vehicle_id: int):
        return list(self.collection.find({"vehicle_id": vehicle_id}))
