from pymongo import MongoClient
from datetime import datetime

class DriverStateDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="htnhung", collection_name="driver_states"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _generate_state_id(self):
        last_state = self.collection.find_one(sort=[("state_id", -1)])
        if last_state and "state_id" in last_state:
            return last_state["state_id"] + 1
        return 1

    def add_driver_state(self, driver_id: int, vehicle_id: int, timestamp: str, status: str, image_url):
        state_id = self._generate_state_id()
        now = datetime.now()
        state_data = {
            "state_id": state_id,
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "status": status,
            "image_url": image_url,
        }
        result = self.collection.insert_one(state_data)
        return str(result.inserted_id), state_id

    def delete_driver_state(self, state_id: int):
        result = self.collection.delete_one({"state_id": state_id})
        return result.deleted_count

    def get_driver_state(self, state_id: int):
        state = self.collection.find_one({"state_id": state_id})
        return state

    def list_driver_states(self):
        return list(self.collection.find())
