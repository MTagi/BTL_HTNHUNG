import cv2
import time
import argparse
import numpy as np
# from mqtt_client import publish_detection
import dlib
from imutils import face_utils
# EAR calculation
from scipy.spatial import distance as dist

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


class DrowsinessDetection:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("drowsiness_detection/shape_predictor_68_face_landmarks.dat")
    def detect_drowsiness(self, frame, mode):
        if mode == "dlib":
            return self.detect_drowsiness_use(frame)
        
    def detect_drowsiness_use_dlib(self, frame):
        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        EAR_THRESHOLD = 0.25
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        for face in faces:
            shape = self.predictor(gray, face)
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            ear = (eye_aspect_ratio(leftEye) + eye_aspect_ratio(rightEye)) / 2.0

            cv2.drawContours(frame, [cv2.convexHull(leftEye)], -1, (0,255,0), 1)
            cv2.drawContours(frame, [cv2.convexHull(rightEye)], -1, (0,255,0), 1)

            if ear < EAR_THRESHOLD:
                return True, frame
            else:
                return False, frame      
        return False, frame          