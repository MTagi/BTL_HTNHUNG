import torch
from ultralytics import YOLO
from torchvision import transforms
import cv2
import numpy as np
import torch
from torchvision import transforms
import numpy as np
import cv2
from .iresnet import iresnet100
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Tuple, List
class FaceRecognition:
    """
    Class for face recognition using a pre-trained model.
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_detect =  YOLO("face_recognition/weights/yolov8n-face.pt")
        self.weight = torch.load("face_recognition/weights/arcface_r100.pth", map_location = self.device)
        self.model_emb = iresnet100()
        self.model_emb.load_state_dict(self.weight)
        self.model_emb.to(self.device)
        self.model_emb.eval()

    def detect_face(self, frame):
        "Trả về list các khuôn mặt phát hiện được trong ảnh"
        conf_thres = 0.4
        iou_thres = 0.5
        list_face = []
        with torch.no_grad():
            result = self.model_detect.predict(frame, conf=conf_thres, iou=iou_thres)
            for box in result[0].boxes.xyxy:  # Duyệt qua từng khuôn mặt phát hiện
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                face_crop = frame[y1:y2, x1:x2]
                list_face.append(face_crop)
        return list_face

    def detect_face_v1(self, frame):
        "Trả về list vị trí các khuôn mặt phát hiện được trong ảnh dưới dạng tuple (x1, y1, x2, y2)"
        conf_thres = 0.4
        iou_thres = 0.5
        list_face = []
        with torch.no_grad():
            result = self.model_detect(frame, conf=conf_thres, iou=iou_thres)
            for box in result[0].boxes.xyxy:  # Duyệt qua từng khuôn mặt phát hiện
                x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                list_face.append((x1, y1, x2, y2))
        return list_face
    
    @torch.no_grad()
    def get_feature(self, face_image):
        """
        Extract features from a face image.

        Args:
            face_image: The input face image.

        Returns:
            numpy.ndarray: The extracted features.
        """
        face_preprocess = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Resize((112, 112)),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        )
        # Convert to RGB
        face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

        # Preprocess image (BGR)
        face_image = face_preprocess(face_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            # Inference to get feature
            emb_img_face = self.model_emb(face_image).cpu().numpy()

        # Convert to array
        images_emb = emb_img_face / np.linalg.norm(emb_img_face)

        return images_emb
    # Hàm tạo embedding_face từ ảnh
    def create_embedding(self, image_path):
        image_face = cv2.imread(image_path)
        result = self.detect_face(image_face)
        face_embedding = self.get_feature(result[0])
        return face_embedding
    def compare_encodings(self, encoding, encodings):
        "Đưa vào 1 vector và 1 list các vector, trả về độ tương đồng và chỉ số của vector có độ tương đồng cao nhất"
        sims = np.dot(encodings, encoding.T)  # Tính độ tương đồng (cosine similarity)
        pare_index = np.argmax(sims)  # Lấy chỉ số của vector có độ tương đồng cao nhất
        score = sims[pare_index]  # Lấy độ tương đồng
        return score, pare_index

    def compare_encodings_v2(self, encoding: np.ndarray, encodings: np.ndarray) -> Tuple[float, int]:
        """
        Đưa vào 1 vector và 1 list/array các vector, trả về độ tương đồng cosine cao nhất
        và chỉ số của vector tương ứng (sử dụng sklearn).

        Args:
            encoding: Vector embedding đơn (1D array hoặc 2D array [1, D]).
            encodings: Mảng các vector embeddings (2D array [N, D]).

        Returns:
            Tuple[float, int]: (Độ tương đồng cosine cao nhất, Chỉ số của vector tương ứng).
        """
        # Đảm bảo encoding có dạng [1, D] để tương thích với cosine_similarity
        if encoding.ndim == 1:
            encoding_2d = encoding.reshape(1, -1)
        elif encoding.shape[0] == 1:
            encoding_2d = encoding
        else:
            raise ValueError("`encoding` phải là vector 1D hoặc 2D array shape [1, D]")
        
        encodings = np.array(encodings[0])

        # --- Tính Cosine Similarity trực tiếp ---
        # cosine_similarity yêu cầu cả 2 input là 2D arrays
        # Kết quả trả về là 2D array [[sim1, sim2, ...]]
        sims_matrix = cosine_similarity(encoding_2d, encodings) # Shape: [1, N]
        sims = sims_matrix.flatten() # Chuyển về 1D array [N]
        # --------------------------------------

        pare_index = np.argmax(sims)  # Lấy chỉ số của vector có độ tương đồng cao nhất
        score = sims[pare_index]      # Lấy độ tương đồng cao nhất
        return float(score), int(pare_index)

        

