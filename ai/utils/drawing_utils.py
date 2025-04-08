import cv2 as cv
import numpy as np

class DrawingUtils:
    """Utility class for drawing operations for visualization in the microsleep detection system."""

    @staticmethod
    def draw_text_with_bg(
        frame, 
        text, 
        pos, 
        font=cv.FONT_HERSHEY_SIMPLEX, 
        font_scale=0.7, 
        thickness=2, 
        bg_color=(255, 255, 255),
        text_color=(0, 0, 0)
    ):
        """
        Draw text with a background rectangle for better visibility.
        
        Args:
            frame (np.ndarray): Input image
            text (str): Text to display
            pos (tuple): Position (x, y) for text
            font: OpenCV font
            font_scale (float): Font size scale
            thickness (int): Line thickness
            bg_color (tuple): Background color in BGR
            text_color (tuple): Text color in BGR
        """
        # Get text dimensions
        (text_width, text_height), baseline = cv.getTextSize(text, font, font_scale, thickness)
        x, y = pos
        
        # Draw background rectangle
        cv.rectangle(
            frame, 
            (x, y - text_height - baseline), 
            (x + text_width, y + baseline), 
            bg_color, 
            cv.FILLED
        )
        
        # Draw text
        cv.putText(
            frame, 
            text, 
            (x, y), 
            font, 
            font_scale, 
            text_color, 
            thickness, 
            lineType=cv.LINE_AA
        )

    @staticmethod
    def draw_status_box(
        frame, 
        status, 
        pos=(10, 30), 
        size=(200, 60), 
        normal_color=(0, 255, 0), 
        warning_color=(0, 255, 255), 
        alert_color=(0, 0, 255)
    ):
        """
        Draw a status box with color-coded information.
        
        Args:
            frame (np.ndarray): Input image
            status (str): Status text ("NORMAL", "WARNING", "ALERT")
            pos (tuple): Position (x, y) for box
            size (tuple): Size (width, height) of box
            normal_color (tuple): Color for normal status
            warning_color (tuple): Color for warning status
            alert_color (tuple): Color for alert status
        """
        x, y = pos
        width, height = size
        
        # Determine color based on status
        color_map = {
            "NORMAL": normal_color,
            "WARNING": warning_color,
            "ALERT": alert_color,
            "DROWSY": warning_color,
            "MICROSLEEP": alert_color
        }
        
        color = color_map.get(status.upper(), normal_color)
        
        # Draw box
        cv.rectangle(frame, (x, y), (x + width, y + height), color, cv.FILLED)
        cv.rectangle(frame, (x, y), (x + width, y + height), (255, 255, 255), 2)
        
        # Draw text
        text_x = x + 10
        text_y = y + height // 2 + 5
        cv.putText(
            frame, 
            status, 
            (text_x, text_y), 
            cv.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 0, 0), 
            2, 
            cv.LINE_AA
        )

    @staticmethod
    def draw_progress_bar(
        frame, 
        value, 
        max_value, 
        pos=(10, 30), 
        size=(200, 20), 
        bg_color=(200, 200, 200), 
        fg_color=(0, 255, 0), 
        border_color=(0, 0, 0)
    ):
        """
        Draw a progress bar.
        
        Args:
            frame (np.ndarray): Input image
            value (float): Current value
            max_value (float): Maximum value
            pos (tuple): Position (x, y) for bar
            size (tuple): Size (width, height) of bar
            bg_color (tuple): Background color
            fg_color (tuple): Foreground color (filled portion)
            border_color (tuple): Border color
        """
        x, y = pos
        width, height = size
        
        # Calculate fill width
        fill_width = int((value / max_value) * width) if max_value > 0 else 0
        fill_width = max(0, min(fill_width, width))  # Clamp
        
        # Draw background
        cv.rectangle(frame, (x, y), (x + width, y + height), bg_color, cv.FILLED)
        
        # Draw filled portion
        cv.rectangle(frame, (x, y), (x + fill_width, y + height), fg_color, cv.FILLED)
        
        # Draw border
        cv.rectangle(frame, (x, y), (x + width, y + height), border_color, 1)

    @staticmethod
    def draw_attention_rectangle(
        frame, 
        landmarks, 
        landmark_indices, 
        padding=10, 
        color=(0, 255, 0), 
        thickness=2
    ):
        """
        Draw a rectangle around specified landmarks.
        
        Args:
            frame (np.ndarray): Input image
            landmarks (dict): Dictionary of facial landmarks
            landmark_indices (list): List of indices to include in the rectangle
            padding (int): Padding around landmarks
            color (tuple): Rectangle color
            thickness (int): Line thickness
        """
        # Check if all landmarks are present
        if not all(idx in landmarks for idx in landmark_indices):
            return
            
        # Get coordinates of landmarks
        x_coords = [landmarks[idx][0] for idx in landmark_indices]
        y_coords = [landmarks[idx][1] for idx in landmark_indices]
        
        # Calculate bounding box with padding
        x_min = max(0, min(x_coords) - padding)
        y_min = max(0, min(y_coords) - padding)
        x_max = min(frame.shape[1], max(x_coords) + padding)
        y_max = min(frame.shape[0], max(y_coords) + padding)
        
        # Draw rectangle
        cv.rectangle(frame, (x_min, y_min), (x_max, y_max), color, thickness)

    @staticmethod
    def draw_alarm_overlay(frame, alpha=0.4):
        """
        Draw a semi-transparent red overlay for alarm state.
        
        Args:
            frame (np.ndarray): Input image
            alpha (float): Transparency level (0-1)
        """
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Fill with red
        cv.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), cv.FILLED)
        
        # Blend with original
        cv.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    @staticmethod
    def add_timestamp(frame, timestamp=None, pos=(10, 30), color=(255, 255, 255)):
        """
        Add a timestamp to the frame.
        
        Args:
            frame (np.ndarray): Input image
            timestamp (float): Timestamp in seconds (if None, current time will be used)
            pos (tuple): Position (x, y) for text
            color (tuple): Text color
        """
        if timestamp is None:
            import time
            timestamp = time.time()
            
        # Format timestamp
        from datetime import datetime
        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # Draw text
        cv.putText(
            frame, 
            time_str, 
            pos, 
            cv.FONT_HERSHEY_SIMPLEX, 
            0.5, 
            color, 
            1, 
            cv.LINE_AA
        )