from flask import Flask, Response
import cv2
import os
import requests
from urllib.parse import urlparse
from flask_cors import CORS
from face_recognition.FaceRecogniton import FaceRecognition
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Cho phép tất cả origins truy cập vào API

# Khởi tạo camera (0 là mặc định webcam đầu tiên)
camera = cv2.VideoCapture(0)

CONSEC_FRAMES = 3
COUNTER = 0
STATUS = False
DRIVER_ID = None
VEHICLE_ID = None
ATTENDANCE_ID = None
SERVER_IP = "http://localhost:5000"  # Địa chỉ IP của server Flask

import time
def process_frame_v1(frame):
    global COUNTER, CONSEC_FRAMES
    from drowsiness_detection.drowsiness_with_dlib import dlib_detector
    drowsy, frame = dlib_detector(frame)
    if drowsy:
        print(COUNTER)
        COUNTER += 1
        if COUNTER >= CONSEC_FRAMES:
            STATUS = True
            cv2.putText(frame, "BUON NGU!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if DRIVER_ID is not None: 
                pass # Gọi API để thêm buon ngu
    else: 
        COUNTER = 0
        STATUS = False
    return frame

def generate_frames():
    while True:
        # Đọc frame từ camera
        success, frame = camera.read()
        if not success:
            break
        else:
            # Xử lý frame trước khi gửi lên web
            processed_frame = process_frame_v1(frame)

            # Mã hóa frame đã xử lý thành JPEG
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame = buffer.tobytes()

            # Trả về frame theo chuẩn multipart
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def get_driver_id():
    global DRIVER_ID
    success, frame = camera.read()
    # Encode frame sang JPEG
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        print("Không thể mã hóa frame")
        DRIVER_ID = None
        
    # Gửi frame dưới dạng file ảnh
    files = {'image': ('frame.jpg', buffer.tobytes(), 'image/jpeg')}
    try:
        response = requests.post(SERVER_IP, files=files)
        data = response.json()
        if response.status_code == 200 and 'driver_id' in data:
            DRIVER_ID = data['driver_id']
    except Exception as e:
        print("❌ Lỗi khi gửi ảnh:", e)
        DRIVER_ID = None
    DRIVER_ID = None
def get_vehicle_id():
    global VEHICLE_ID
    from mqtt import get_vehicle_id
    VEHICLE_ID = get_vehicle_id()

from apscheduler.schedulers.background import BackgroundScheduler
def reset_attendance_id():
    global ATTENDANCE_ID
    ATTENDANCE_ID = None

# Hàm để thêm điểm danh
def add_attendance(driver_id, vehicle_id, date):
    checkin_time = datetime.now().time().isoformat()
    attendance_data = {
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "note": "Điểm danh mới",
        "checkin_time": checkin_time,
        "checkout_time": None
    }
    response = requests.post("http://localhost:5000/attendances/add", json=attendance_data)
    
    if response.status_code == 200:
        print("Thêm điểm danh thành công.")
    else:
        print(f"Lỗi khi thêm điểm danh: {response.status_code}, {response.text}")

# Hàm để cập nhật điểm danh
def update_attendance(attendance_id, driver_id, vehicle_id, checkin_time, checkout_time, note):
    update_data = {
        "attendance_id": attendance_id,
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "checkin_time": checkin_time,
        "checkout_time": checkout_time,
        "note": note
    }
    response = requests.post("http://localhost:5000/attendances/update", json=update_data)
    
    if response.status_code == 200:
        print("Cập nhật điểm danh thành công.")
    else:
        print(f"Lỗi khi cập nhật điểm danh: {response.status_code}, {response.text}")
# HÀM GỌI API
def save_infor():
    get_driver_id()
    if DRIVER_ID is None:
        print("❌ Không thể điểm danh")
    else: 
        from datetime import datetime
        date = datetime.now().date().isoformat()
        ATTENDANCE_API_URL = "http://localhost:5000/attendances/search"  # Địa chỉ API điểm danh
        # Gọi API tìm điểm danh của tài xế và xe theo driver_id, vehicle_id, và date
        response = requests.post(ATTENDANCE_API_URL, json={
            "driver_id": DRIVER_ID,
            "vehicle_id": VEHICLE_ID,
            "date": date
        })
        # Nếu điểm danh không có (404), thực hiện thêm điểm danh mới
        if response.status_code == 404:
            print("Không tìm thấy điểm danh, thêm mới.")
            add_attendance(DRIVER_ID, VEHICLE_ID, date)
        elif response.status_code == 200:
            # Nếu điểm danh đã có, cập nhật thời gian checkout
            attendance = response.json()
            print("Điểm danh đã có, cập nhật checkout_time.")
            update_attendance(attendance['attendance_id'], DRIVER_ID, VEHICLE_ID, attendance['checkin_time'], datetime.now().time().isoformat(), attendance['note'])
        else:
            print(f"Lỗi khi gọi API điểm danh: {response.status_code}, {response.text}")
        from mqtt import get_position
        lat, long = get_position()
        # Gọi API để thêm vị trí tài xế
        location_data = {
                'driver_id': 'D001',
                'vehicle_id': 'V001',
                'latitude': lat,
                'longitude': long
            }
        url = 'http://localhost:5000/driver_locations/add'
        try:
            response = requests.post(url, json=location_data)
            if response.status_code == 200:
                print("✅ Vị trí tài xế đã được thêm thành công.")
            else:
                print(f"❌ Lỗi khi thêm vị trí tài xế: {response.status_code}, {response.text}")
        except Exception as e:
            print("❌ Lỗi khi gọi API:", e)
    try:
        print("⏰ Đang gọi API...")
        response = requests.get("http://localhost:5000/my-task")  # đổi URL phù hợp
        print("✅ Phản hồi:", response.status_code, response.text)
    except Exception as e:
        print("❌ Lỗi:", e)

# TẠO LỊCH GỌI ĐỊNH KỲ
scheduler = BackgroundScheduler()
scheduler.add_job(save_infor, 'interval', minutes=5)
scheduler.add_job(func=reset_attendance_id, trigger="cron", hour=0, minute=0)
scheduler.start()

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
