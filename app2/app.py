from flask import Flask, Response
import cv2
import os
import requests
from urllib.parse import urlparse
from flask_cors import CORS
import base64
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
CORS(app)  # Cho phép tất cả origins truy cập vào API

# Khởi tạo camera (0 là mặc định webcam đầu tiên)
camera = cv2.VideoCapture(0)

from face_recognition.FaceRecogniton import FaceRecognition
FaceReco = FaceRecognition()
from model.DriverDatabase import DriverDatabase
driver_db = DriverDatabase()


@app.route('/get_driver_id', methods=['POST'])
def get_driver_id():
    import numpy as np
    from PIL import Image
    image = request.files.get('image')
    image = Image.open(image.stream).convert('RGB')
    image_np = np.array(image)
    list_faces = FaceReco.detect_face(image_np)
    if list_faces == []:
        return jsonify({"status": "error", "message": "Không phát hiện khuôn mặt!"})
    else: 
        # Lấy embedding của khuôn mặt đầu tiên
        face_image = list_faces[0]
        image_emb = FaceReco.get_feature(face_image)
        list_drivers = driver_db.list_drivers()
        list_emb = [d['image_emb'] for d in list_drivers]
        if(len(list_emb) == 0):
            return jsonify({"status": "error", "message": "Không có tài xế nào trong hệ thống!"})
        else: 
            # Tính độ tương đồng với tất cả các embedding trong database
            score, index = FaceReco.compare_encodings_v2(image_emb, list_emb)
            print(score)
            print("aaaaaaaaaaaaa")
            if score < 0.5:
                return jsonify({"status": "error", "message": "Không tìm thấy tài xế!"})
            else:
                driver_id = list_drivers[index]['driver_id']
                print(driver_id)
                return jsonify({"status": "success", "driver_id": driver_id})    

#Các api liên quan đến quản lý tài xế. 
from model.VehicleDatabase import VehicleDatabase
from flask import Flask, request, jsonify

vehicle_db = VehicleDatabase()

# Lấy danh sách vehicles
@app.route('/vehicles', methods=['GET'])
def list_vehicles():
    vehicles = vehicle_db.list_vehicles()
    for v in vehicles:
        v['_id'] = str(v['_id'])
    return jsonify(vehicles)

# Lấy chi tiết 1 vehicle
@app.route('/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    vehicle = vehicle_db.get_vehicle(vehicle_id)
    if not vehicle:
        return jsonify({'error': 'Không tìm thấy vehicle'}), 404
    vehicle['_id'] = str(vehicle['_id'])
    return jsonify(vehicle)

# Thêm vehicle
@app.route('/vehicles/add', methods=['POST'])
def add_vehicle():
    data = request.get_json()
    license_plate = data.get('license_plate')
    vehicle_type = data.get('vehicle_type')
    vehicle_ip = data.get('vehicle_ip')
    if not license_plate or not vehicle_type:
        return jsonify({'error': 'Thiếu thông tin'}), 400

    inserted_id, vehicle_id = vehicle_db.add_vehicle(license_plate, vehicle_type, vehicle_ip)
    return jsonify({'message': 'Thêm thành công', 'vehicle_id': vehicle_id})

# Cập nhật vehicle
@app.route('/vehicles/update', methods=['POST'])
def update_vehicle():
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    license_plate = data.get('license_plate')
    vehicle_type = data.get('vehicle_type')
    vehicle_ip = data.get('vehicle_ip')
    if not all([vehicle_id, license_plate, vehicle_type, vehicle_ip]):
        return jsonify({'error': 'Thiếu thông tin'}), 400

    modified_count = vehicle_db.update_vehicle(vehicle_id, license_plate, vehicle_type, vehicle_ip)
    if modified_count == 0:
        return jsonify({'error': 'Không tìm thấy vehicle'}), 404
    return jsonify({'message': 'Cập nhật thành công'})

# Xóa vehicle
@app.route('/vehicles/delete', methods=['POST'])
def delete_vehicle():
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    if not vehicle_id:
        return jsonify({'error': 'Thiếu vehicle_id'}), 400

    deleted_count = vehicle_db.delete_vehicle(vehicle_id)
    if deleted_count == 0:
        return jsonify({'error': 'Không tìm thấy vehicle'}), 404
    return jsonify({'message': 'Xóa thành công'})


from model.DriverDatabase import DriverDatabase
driver_db = DriverDatabase()

# Lấy danh sách tài xế
@app.route('/drivers', methods=['GET'])
def list_drivers():
    drivers = driver_db.list_drivers()
    for d in drivers:
        d['_id'] = str(d['_id'])
    return jsonify(drivers)

# Lấy chi tiết 1 tài xế
@app.route('/drivers/<int:driver_id>', methods=['GET'])
def get_driver(driver_id):
    driver = driver_db.get_driver(driver_id)
    if not driver:
        return jsonify({'error': 'Không tìm thấy driver'}), 404
    driver['_id'] = str(driver['_id'])
    return jsonify(driver)


@app.route('/drivers/add', methods=['POST'])
def add_driver():
    name = request.form['name']
    address = request.form['address']
    phone_number = request.form['phone_number']
    image = request.files['image']
    

    # Kiểm tra thông tin
    if not name or not address or not phone_number or not image:
        return jsonify({"status": "error", "message": "Vui lòng nhập đầy đủ thông tin!"})

    # Gọi để lấy driver_id mới (chưa thêm)
    driver_id = driver_db._generate_driver_id()

    # Tạo folder images nếu chưa có
    image_folder = "images"
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    # Lưu ảnh với tên là driver_id.jpg
    image_path = os.path.join(image_folder, f"{driver_id}.jpg")
    image.save(image_path)
    image_emb = FaceReco.create_embedding(image_path)  # Tạo embedding từ ảnh
    # Thêm driver vào MongoDB
    inserted_id, driver_id = driver_db.add_driver(
        name=name,
        address=address,
        image_url=image_path,
        image_emb=image_emb.tolist(),  # Chuyển đổi numpy array thành list
        phone_number=phone_number
    )

    return jsonify({"status": "success", "message": "Thêm driver thành công", "driver_id": driver_id})
@app.route('/drivers/update', methods=['POST'])
def update_driver():
    driver_id = request.form['driver_id']
    name = request.form['name']
    address = request.form['address']
    phone_number = request.form['phone_number']
    image = request.files.get('image')  # Có thể không gửi ảnh

    # Kiểm tra thông tin cơ bản
    if not driver_id or not name or not address or not phone_number:
        return jsonify({"status": "error", "message": "Vui lòng nhập đầy đủ thông tin!"})

    try:
        driver_id = int(driver_id)
    except ValueError:
        return jsonify({"status": "error", "message": "driver_id không hợp lệ!"})

    # Mặc định giữ nguyên ảnh và embedding cũ
    existing_driver = driver_db.get_driver(driver_id)
    if not existing_driver:
        return jsonify({"status": "error", "message": "Không tìm thấy driver!"})

    image_url = existing_driver['image_url']
    image_emb = existing_driver['image_emb']

    # Nếu có ảnh mới thì lưu lại và tính lại embedding
    if image:
        image_folder = "images"
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
        image_path = os.path.join(image_folder, f"{driver_id}.jpg")
        image.save(image_path)
        image_emb = FaceReco.create_embedding(image_path).tolist()
        image_url = image_path

    # Cập nhật vào database
    modified_count = driver_db.update_driver(
        driver_id=driver_id,
        name=name,
        address=address,
        image_url=image_url,
        image_emb=image_emb,
        phone_number=phone_number
    )

    if modified_count == 0:
        return jsonify({"status": "error", "message": "Không có thay đổi nào được cập nhật!"})
    
    return jsonify({"status": "success", "message": "Cập nhật driver thành công"})

# Xóa tài xế
@app.route('/drivers/delete', methods=['POST'])
def delete_driver():
    data = request.get_json()
    driver_id = data.get('driver_id')
    if not driver_id:
        return jsonify({'error': 'Thiếu driver_id'}), 400

    deleted_count = driver_db.delete_driver(driver_id)
    if deleted_count == 0:
        return jsonify({'error': 'Không tìm thấy driver'}), 404
    return jsonify({'message': 'Xóa thành công'})

from model.DriverStateDatabase import DriverStateDatabase  # bạn phải tạo module này như đã có

driver_state_db = DriverStateDatabase()

# Lấy danh sách trạng thái tài xế
@app.route('/driver_states', methods=['GET'])
def list_driver_states():
    states = driver_state_db.list_driver_states()
    for s in states:
        s['_id'] = str(s['_id'])
    return jsonify(states)

# Lấy chi tiết 1 trạng thái
@app.route('/driver_states/<int:state_id>', methods=['GET'])
def get_driver_state(state_id):
    state = driver_state_db.get_driver_state(state_id)
    if not state:
        return jsonify({'error': 'Không tìm thấy trạng thái'}), 404
    state['_id'] = str(state['_id'])
    return jsonify(state)

# name = request.form['name']
#     address = request.form['address']
#     phone_number = request.form['phone_number']
#     image = request.files['image']
    

#     # Kiểm tra thông tin
#     if not name or not address or not phone_number or not image:
#         return jsonify({"status": "error", "message": "Vui lòng nhập đầy đủ thông tin!"})

#     # Gọi để lấy driver_id mới (chưa thêm)
#     driver_id = driver_db._generate_driver_id()

#     # Tạo folder images nếu chưa có
#     image_folder = "images"
#     if not os.path.exists(image_folder):
#         os.makedirs(image_folder)

#     # Lưu ảnh với tên là driver_id.jpg
#     image_path = os.path.join(image_folder, f"{driver_id}.jpg")
#     image.save(image_path)
#     image_emb = FaceReco.create_embedding(image_path)  # Tạo embedding từ ảnh


# Thêm trạng thái tài xế
import traceback
from flask import request, jsonify
import os

@app.route('/driver_states/add', methods=['POST'])
def add_driver_state():
    try:
        driver_id = request.form['driver_id']
        vehicle_id = request.form['vehicle_id']
        timestamp = request.form['timestamp']
        status = request.form['status']
        image = request.files['image']

        if not all([driver_id, vehicle_id, status, image, timestamp]):
            return jsonify({'error': 'Thiếu thông tin'}), 400
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
        # Tạo tên và lưu ảnh
        image_name = f"{driver_id}_{vehicle_id}_{safe_timestamp}"
        image_folder = "images_driver_status"
        os.makedirs(image_folder, exist_ok=True)
        image_path = os.path.join(image_folder, f"{image_name}.jpg")
        image.save(image_path)

        # Gọi hàm thêm vào DB
        inserted_id, state_id = driver_state_db.add_driver_state(
            driver_id, vehicle_id, timestamp, status, image_path
        )

        return jsonify({'message': 'Thêm trạng thái thành công', 'state_id': state_id})

    except KeyError as e:
        return jsonify({'error': f'Missing field: {str(e)}'}), 400
    except Exception as e:
        # Ghi log lỗi đầy đủ (stack trace)
        print("Lỗi xảy ra trong add_driver_state:", str(e))
        traceback.print_exc()
        return jsonify({'error': 'Đã xảy ra lỗi nội bộ'}), 500


from flask import request, jsonify
from model.AttendanceDatabase import AttendanceDatabase  # Import lớp AttendanceDatabase từ model

attendance_db = AttendanceDatabase()

# Lấy danh sách điểm danh
@app.route('/attendances', methods=['GET'])
def list_attendances():
    attendances = attendance_db.list_attendances()
    for a in attendances:
        a['_id'] = str(a['_id'])  # Convert ObjectId thành chuỗi
    return jsonify(attendances)

# Lấy chi tiết điểm danh của tài xế
@app.route('/attendances/<int:attendance_id>', methods=['GET'])
def get_attendance(attendance_id):
    attendance = attendance_db.get_attendance(attendance_id)
    if not attendance:
        return jsonify({'error': 'Không tìm thấy điểm danh'}), 404
    attendance['_id'] = str(attendance['_id'])
    return jsonify(attendance)
@app.route('/attendances/search', methods=['POST'])
def search_attendance():
    # Lấy dữ liệu từ body của request (JSON)
    data = request.get_json()

    # Lấy các tham số từ dữ liệu JSON
    driver_id = data.get('driver_id')
    date = data.get('date')  # Ngày ở dạng 'yyyy-mm-dd'

    if not driver_id  or not date:
        return jsonify({'error': 'Thiếu thông tin (driver_id, vehicle_id, date)'}), 400

    # Tìm điểm danh trong MongoDB với driver_id, vehicle_id và ngày
    attendance = attendance_db.collection.find_one({
        "driver_id": driver_id,
        "date": date
    })

    if not attendance:
        return jsonify({'error': 'Không tìm thấy điểm danh'}), 404

    attendance['_id'] = str(attendance['_id'])  # Convert ObjectId thành chuỗi
    return jsonify(attendance)
# Thêm điểm danh cho tài xế
@app.route('/attendances/add', methods=['POST'])
def add_attendance():
    data = request.get_json()
    driver_id = data.get('driver_id')
    vehicle_id = data.get('vehicle_id')
    note = data.get('note')

    if not all([driver_id, vehicle_id, note]):
        return jsonify({'error': 'Thiếu thông tin'}), 400

    inserted_id, attendance_id = attendance_db.add_attendance(driver_id, vehicle_id, note)
    return jsonify({'message': 'Điểm danh thành công', 'attendance_id': attendance_id})

# Cập nhật điểm danh
@app.route('/attendances/update', methods=['POST'])
def update_attendance():
    data = request.get_json()
    attendance_id = data.get('attendance_id')
    driver_id = data.get('driver_id')
    vehicle_id = data.get('vehicle_id')
    checkin_time = data.get('checkin_time')
    checkout_time = data.get('checkout_time')
    note = data.get('note')

    if not all([attendance_id, driver_id, vehicle_id, checkin_time, checkout_time, note]):
        return jsonify({'error': 'Thiếu thông tin'}), 400

    modified_count = attendance_db.update_attendance(attendance_id, driver_id, vehicle_id, checkin_time, checkout_time, note)
    if modified_count == 0:
        return jsonify({'error': 'Không tìm thấy điểm danh'}), 404
    return jsonify({'message': 'Cập nhật điểm danh thành công'})



from model.DriverLocationDatabase import DriverLocationDatabase  # bạn phải tạo module này như đã có

driver_location_db = DriverLocationDatabase()

# Lấy danh sách vị trí tài xế
@app.route('/driver_locations', methods=['GET'])
def list_driver_locations():
    locations = driver_location_db.list_driver_locations()
    for l in locations:
        l['_id'] = str(l['_id'])
    return jsonify(locations)

# Lấy chi tiết 1 vị trí
@app.route('/driver_locations/<int:location_id>', methods=['GET'])
def get_driver_location(location_id):
    location = driver_location_db.get_driver_location(location_id)
    if not location:
        return jsonify({'error': 'Không tìm thấy vị trí tài xế'}), 404
    location['_id'] = str(location['_id'])
    return jsonify(location)

# Thêm vị trí tài xế
@app.route('/driver_locations/add', methods=['POST'])
def add_driver_location():
    data = request.get_json()
    driver_id = data.get('driver_id')
    vehicle_id = data.get('vehicle_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not all([driver_id, vehicle_id, latitude, longitude]):
        return jsonify({'error': 'Thiếu thông tin'}), 400

    inserted_id, location_id = driver_location_db.add_driver_location(driver_id, vehicle_id, latitude, longitude)
    return jsonify({'message': 'Thêm vị trí tài xế thành công', 'location_id': location_id})

@app.route('/get_image', methods=['POST'])
def get_image_base64():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Missing image path in request body'}), 400

    image_path = data['path']
    try:
        with open(image_path, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        return jsonify({'image_base64': b64_string})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Camera Stream</title>
        </head>
        <body>
            <h1>Live Camera Streaming with Processing</h1>
            <img src="/video" width="800" height="600">
        </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

