import cv2 as cv
import mediapipe as mp
import numpy as np

class FaceMeshGenerator:
    """
    A class to detect and create face mesh landmarks using MediaPipe.
    
    This class handles the creation of facial landmark detections from video frames,
    which are then used for eye aspect ratio calculations and microsleep detection.
    """
    
    def __init__(self, mode=False, max_faces=1, min_detection_con=0.5, min_track_con=0.5):
        """
        Initialize the FaceMeshGenerator with specified parameters.
        
        Args:
            mode (bool): Whether to use static mode (True) or video mode (False)
            max_faces (int): Maximum number of faces to detect
            min_detection_con (float): Minimum detection confidence threshold
            min_track_con (float): Minimum tracking confidence threshold
        """
        self.mode = mode
        self.max_faces = max_faces
        self.min_detection_con = min_detection_con
        self.min_track_con = min_track_con
        
        # Initialize MediaPipe face mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=self.mode,
            max_num_faces=self.max_faces,
            min_detection_confidence=self.min_detection_con,
            min_tracking_confidence=self.min_track_con
        )
        
        # Initialize drawing utilities
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize results container
        self.results = None

    def create_face_mesh(self, frame, draw=True):
        """
        Process a frame and create face mesh landmarks.
        
        Args:
            frame (np.ndarray): Input video frame
            draw (bool): Whether to draw the landmarks on the frame
            
        Returns:
            tuple: (processed_frame, landmarks_dict)
                   landmarks_dict is a dictionary mapping landmark indices to (x,y) coordinates
        """
        # Create a copy of the frame
        img = frame.copy()
        
        # Convert to RGB for MediaPipe
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        
        # Process the image
        self.results = self.face_mesh.process(img_rgb)
        
        # Initialize empty landmarks dictionary
        landmarks_dict = {}
        
        # If facial landmarks are detected
        if self.results.multi_face_landmarks:
            # Get the first face (we only support one face at a time for microsleep detection)
            face_landmarks = self.results.multi_face_landmarks[0]
            
            # Get image dimensions
            img_h, img_w, _ = img.shape
            
            # Extract landmark coordinates and store in dictionary
            for idx, landmark in enumerate(face_landmarks.landmark):
                # Convert normalized coordinates to pixel coordinates
                x, y = int(landmark.x * img_w), int(landmark.y * img_h)
                landmarks_dict[idx] = (x, y)
            
            # Draw the landmarks if requested
            if draw:
                self._draw_landmarks(img, face_landmarks)
        
        return img, landmarks_dict

    def _draw_landmarks(self, img, face_landmarks):
        """
        Draw facial landmarks on the image.
        
        Args:
            img (np.ndarray): Input image
            face_landmarks: MediaPipe face landmarks
        """
        # Draw face mesh with default parameters
        self.mp_drawing.draw_landmarks(
            image=img,
            landmark_list=face_landmarks,
            connections=self.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
        )
        
        # Draw contours
        self.mp_drawing.draw_landmarks(
            image=img,
            landmark_list=face_landmarks,
            connections=self.mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
        )
        
        # Draw irises if available in the model
        if hasattr(self.mp_face_mesh, 'FACEMESH_IRISES'):
            self.mp_drawing.draw_landmarks(
                image=img,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_IRISES,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style()
            )

    @staticmethod
    def extract_eye_region(frame, landmarks, eye_landmarks, padding=10):
        """
        Extract the eye region from the frame using landmarks.
        
        This is useful for focused analysis of eye regions.
        
        Args:
            frame (np.ndarray): Input frame
            landmarks (dict): Dictionary of facial landmarks
            eye_landmarks (list): List of landmark indices for the eye
            padding (int): Padding around the eye region
            
        Returns:
            np.ndarray: Cropped eye region
        """
        # Check if all required landmarks are present
        if not all(lm in landmarks for lm in eye_landmarks):
            return None
            
        # Get coordinates
        x_coords = [landmarks[lm][0] for lm in eye_landmarks]
        y_coords = [landmarks[lm][1] for lm in eye_landmarks]
        
        # Calculate bounding box with padding
        x_min = max(0, min(x_coords) - padding)
        y_min = max(0, min(y_coords) - padding)
        x_max = min(frame.shape[1], max(x_coords) + padding)
        y_max = min(frame.shape[0], max(y_coords) + padding)
        
        # Extract region
        eye_region = frame[y_min:y_max, x_min:x_max]
        
        return eye_region if eye_region.size > 0 else None