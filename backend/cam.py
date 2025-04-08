import cv2
import sys
import requests

def send_to_server(face_count, eye_count):
    try:
        url = "http://localhost:5000/vision" # Replace with your server URL or online server
        payload = {
            "face_count": face_count,
            "eye_count": eye_count
        }
        response = requests.post(url, json=payload)
        print(f"Sent to server: {payload}, Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send data: {e}")

def eye_detection():
    # Load the pre-trained eye detector (Haar cascade classifier)
    # Use the more accurate eye detector with glasses support
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
    # Load the pre-trained face detector (LBP is faster, Haar is more accurate)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
    
    # Check if the cascade classifiers were loaded correctly
    if eye_cascade.empty():
        print("Error: Could not load eye cascade classifier")
        return
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier")
        return
    
    # Initialize webcam (0 is usually the default camera)
    cap = cv2.VideoCapture("http://192.168.18.216:81/stream") # Replace with your camera URL
    # cap = cv2.VideoCapture(0)  # Uncomment this line to use the default webcam
    
    # Try to set higher resolution for better detection
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Check if the webcam opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("Eye detection started. Press 'q' to quit.")
    
    while True:
        # Read frame from webcam
        ret, frame = cap.read()
        
        # If frame is not read correctly
        if not ret:
            print("Error: Failed to capture image")
            break
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization to improve contrast
        gray = cv2.equalizeHist(gray)
        
        # Apply mild Gaussian blur to reduce noise (helps with detection)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect faces in the grayscale frame with improved parameters
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,  # Smaller scale factor for better accuracy (but slower)
            minNeighbors=6,    # Higher value reduces false positives
            minSize=(60, 60),  # Minimum face size (adjusted for typical webcam distance)
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Draw blue rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)  # Blue color (BGR)
            cv2.putText(frame, 'Face', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Create a region of interest for eyes within the face
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            # Apply additional contrast enhancement to the face region
            roi_gray = cv2.equalizeHist(roi_gray)
            
            # Use more accurate parameters for eye detection within face
            eyes = eye_cascade.detectMultiScale(
                roi_gray,
                scaleFactor=1.03,     # Smaller scale factor for better detection
                minNeighbors=8,       # Higher value reduces false positives
                minSize=(25, 25),     # Minimum eye size
                maxSize=(80, 80),     # Maximum eye size (prevents false detections that are too large)
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Draw green rectangles around detected eyes within the face
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)  # Green color
                cv2.putText(roi_color, 'Eye', (ex, ey-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Display number of faces and eyes detected
        cv2.putText(frame, f'Faces detected: {len(faces)}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
        # Look for eyes outside faces with stricter parameters to avoid false positives
        eyes_outside = eye_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=10,      # Very strict to prevent false positives
            minSize=(30, 30),
            maxSize=(70, 70),     # Maximum reasonable eye size
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Draw rectangles around detected eyes outside faces
        for (x, y, w, h) in eyes_outside:
            # Check if this eye is within a face (to avoid duplicates)
            is_within_face = False
            for (fx, fy, fw, fh) in faces:
                if x >= fx and y >= fy and x + w <= fx + fw and y + h <= fy + fh:
                    is_within_face = True
                    break
            
            # Only draw if not within a face
            if not is_within_face:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'Eye', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Count eyes more accurately
        total_eyes = 0
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            eyes_in_face = eye_cascade.detectMultiScale(
                face_roi,
                scaleFactor=1.03,
                minNeighbors=8,
                minSize=(25, 25),
                maxSize=(80, 80)
            )
            total_eyes += len(eyes_in_face)
        cv2.putText(frame, f'Eyes detected: {total_eyes}', (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        send_to_server(len(faces), total_eyes)

        # Display the resulting frame
        cv2.imshow('Eye Detection', frame)
        
        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    eye_detection()