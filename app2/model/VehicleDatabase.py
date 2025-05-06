from pymongo import MongoClient

class VehicleDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="htnhung", collection_name="vehicles"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _generate_vehicle_id(self):
        """
        Tự động tạo vehicle_id mới: lấy vehicle_id lớn nhất + 1.
        Nếu chưa có vehicle nào, trả về 1.
        """
        last_vehicle = self.collection.find_one(sort=[("vehicle_id", -1)])
        if last_vehicle and "vehicle_id" in last_vehicle:
            return last_vehicle["vehicle_id"] + 1
        return 1

    def add_vehicle(self, license_plate: str, vehicle_type: str, vehicle_ip: str):
        """
        Thêm vehicle mới với các tham số riêng.
        vehicle_id tự động sinh.
        """
        vehicle_id = self._generate_vehicle_id()
        vehicle_data = {
            "vehicle_id": vehicle_id,
            "license_plate": license_plate,
            "vehicle_type": vehicle_type, 
            "vehicle_ip": vehicle_ip

        }
        result = self.collection.insert_one(vehicle_data)
        return str(result.inserted_id), vehicle_id

    def update_vehicle(self, vehicle_id: int, license_plate: str, vehicle_type: str, vehicle_ip: str):
        """
        Cập nhật vehicle theo vehicle_id.
        """
        update_data = {
            "license_plate": license_plate,
            "vehicle_type": vehicle_type, 
            "vehicle_ip": vehicle_ip
        }
        result = self.collection.update_one(
            {"vehicle_id": vehicle_id},
            {"$set": update_data}
        )
        return result.modified_count

    def delete_vehicle(self, vehicle_id: int):
        """
        Xóa vehicle theo vehicle_id.
        """
        result = self.collection.delete_one({"vehicle_id": vehicle_id})
        return result.deleted_count

    def get_vehicle(self, vehicle_id: int):
        """
        Lấy thông tin vehicle theo vehicle_id.
        """
        vehicle = self.collection.find_one({"vehicle_id": vehicle_id})
        return vehicle

    def list_vehicles(self):
        """
        Lấy danh sách tất cả vehicles.
        """
        return list(self.collection.find())

# # Ví dụ sử dụng:
# if __name__ == "__main__":
#     db = VehicleDatabase()

#     # Thêm vehicle mới
#     inserted_id, vehicle_id = db.add_vehicle(
#         license_plate="51A-12345",
#         vehicle_type="Car"
#     )
#     print(f"Đã thêm vehicle MongoID: {inserted_id}, vehicle_id: {vehicle_id}")

#     # Sửa vehicle
#     modified_count = db.update_vehicle(
#         vehicle_id=vehicle_id,
#         license_plate="51B-67890",
#         vehicle_type="Truck"
#     )
#     print(f"Đã sửa {modified_count} vehicle")

#     # Xóa vehicle
#     deleted_count = db.delete_vehicle(vehicle_id)
#     print(f"Đã xóa {deleted_count} vehicle")
