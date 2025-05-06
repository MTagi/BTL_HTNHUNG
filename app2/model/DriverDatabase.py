from pymongo import MongoClient

class DriverDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="htnhung", collection_name="drivers"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def _generate_driver_id(self):
        """
        Tự động tạo driver_id mới: lấy driver_id lớn nhất + 1.
        Nếu chưa có driver nào, trả về 1.
        """
        last_driver = self.collection.find_one(sort=[("driver_id", -1)])
        if last_driver and "driver_id" in last_driver:
            return last_driver["driver_id"] + 1
        return 1

    def add_driver(self, name: str, address: str, image_url: str, image_emb: list, phone_number: str):
        """
        Thêm driver mới với các tham số riêng.
        driver_id tự động sinh.
        """
        driver_id = self._generate_driver_id()
        driver_data = {
            "driver_id": driver_id,
            "name": name,
            "address": address,
            "image_url": image_url,
            "image_emb": image_emb,
            "phone_number": phone_number
        }
        result = self.collection.insert_one(driver_data)
        return str(result.inserted_id), driver_id

    def update_driver(self, driver_id: int, name: str, address: str, image_url: str, image_emb: list, phone_number: str):
        """
        Cập nhật driver theo driver_id với từng tham số riêng biệt.
        """
        update_data = {
            "name": name,
            "address": address,
            "image_url": image_url,
            "image_emb": image_emb,
            "phone_number": phone_number
        }
        result = self.collection.update_one(
            {"driver_id": driver_id},
            {"$set": update_data}
        )
        return result.modified_count

    def delete_driver(self, driver_id: int):
        """
        Xóa driver theo driver_id.
        """
        result = self.collection.delete_one({"driver_id": driver_id})
        return result.deleted_count

    def get_driver(self, driver_id: int):
        """
        Lấy thông tin driver theo driver_id.
        """
        driver = self.collection.find_one({"driver_id": driver_id})
        return driver

    def list_drivers(self):
        """
        Lấy danh sách tất cả drivers.
        """
        return list(self.collection.find())

# # Ví dụ sử dụng:
# if __name__ == "__main__":
#     db = DriverDatabase()

#     # # Thêm driver mới
#     inserted_id, driver_id = db.add_driver(
#         name="Nguyen Van A",
#         address="123 ABC Street",
#         image_url="http://example.com/image.jpg",
#         image_emb=[0.1, 0.2, 0.3, 0.4],
#         phone_number="0909123456"
#     )
#     # print(f"Đã thêm driver MongoID: {inserted_id}, driver_id: {driver_id}")

#     # Sửa driver
#     modified_count = db.update_driver(
#         driver_id=driver_id,
#         name="Nguyen Van A Updated",
#         address="456 XYZ Avenue",
#         image_url="http://example.com/image2.jpg",
#         image_emb=[0.5, 0.6, 0.7, 0.8],
#         phone_number="0912345678"
#     )
#     # print(f"Đã sửa {modified_count} driver")

#     # # Xóa driver
#     # deleted_count = db.delete_driver(driver_id)
#     # print(f"Đã xóa {deleted_count} driver")
