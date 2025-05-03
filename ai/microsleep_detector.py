import platform
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import time
import os
from datetime import datetime
from collections import deque
import threading
import os
import serial

import requests
os.system("say 'Blink detected'")

from facemesh_module import FaceMeshGenerator
from eye_analyzer import EyeAspectRatioAnalyzer
from utils.drawing_utils import DrawingUtils
from models.microsleep_classifier import MicrosleepClassifier

class MicrosleepDetector:
    """
    An improved class to detect microsleep events in real-time video using facial landmarks
    and machine learning classification of eye movement patterns.
    """
    
    # Define colors for visualization
    COLORS = {
        'GREEN': {'hex': '#56f10d', 'bgr': (13, 241, 86)},
        'BLUE': {'hex': '#0329fc', 'bgr': (252, 41, 3)},
        'RED': {'hex': '#f70202', 'bgr': (2, 2, 247)},
        'YELLOW': {'hex': '#f9e70f', 'bgr': (15, 231, 249)},
        'ORANGE': {'hex': '#ff9900', 'bgr': (0, 153, 255)}
    }
    
    # Alert states
    ALERT_STATES = {
        'NORMAL': 0,
        'BLINK': 1,
        'DROWSY': 2,
        'MICROSLEEP': 3
    }

    def send_serial_signal(self, char='B'):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(char.encode())
                print(f"Sent '{char}' to Arduino.")
            except Exception as e:
                print(f"Failed to write to serial: {e}")

    # Tambahkan parameter baru di __init__ MicrosleepDetector
    def __init__(self, camera_id=0, ear_threshold=0.24, consec_frames=3, 
                microsleep_frames=15, save_video=False, display_plot=True,
                enable_audio=True, sensitivity=0.7, driver_name="Default Driver", 
                armada="Default Armada", rute="Default Rute", server_url="http://127.0.0.1:5001/vision"):
        # Parameter lama
        self.generator = FaceMeshGenerator()
        self.eye_analyzer = EyeAspectRatioAnalyzer()
        self.microsleep_classifier = MicrosleepClassifier()
        self.microsleep_classifier.set_sensitivity(sensitivity)
        
        # Parameter lama
        self.camera_id = camera_id
        self.EAR_THRESHOLD = ear_threshold
        self.CONSEC_FRAMES = consec_frames
        self.MICROSLEEP_FRAMES = microsleep_frames
        self.save_video = save_video
        self.display_plot = display_plot
        self.enable_audio = enable_audio
        self.sensitivity = sensitivity
        
        # Parameter baru
        self.driver_name = driver_name
        self.armada = armada
        self.rute = rute
        self.server_url = server_url
        
        # Initialize capture and output
        self.cap = None
        self.out = None
        self._init_video_capture()
        
        # Tracking variables
        self._init_tracking_variables()
        
        # Initialize plotting if enabled
        if self.display_plot:
            self._init_plot()
            
        # Initialize audio alert
        self.audio_thread = None
        self.last_alert_time = 0
        self.alert_cooldown = 3.0  # seconds between alerts
        
        # Initialize last sent data time
        self.last_data_sent_time = 0
        self.data_send_interval = 1.0  # seconds between data sends

        try:
            self.serial_port = serial.Serial('/dev/tty.SLAB_USBtoUART', 9600, timeout=1)  # Ganti port sesuai sistem kamu
            print("🔌 Serial connection established with ESP32.")
        except Exception as e:
            self.serial_port = None
            print(f"❌ Failed to connect to serial port: {e}")

    def _init_video_capture(self):
        """Initialize video capture from camera"""
        self.cap = cv.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            raise IOError(f"Failed to open camera with ID {self.camera_id}")
            
        # Get capture properties
        self.frame_width = int(self.cap.get(cv.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv.CAP_PROP_FPS))
        if self.fps <= 0:  # Sometimes webcams don't report correct FPS
            self.fps = 30
        
        if self.save_video:
            self._init_video_writer()

    def _init_video_writer(self):
        """Initialize video writer for saving output"""
        # Create output directory if it doesn't exist
        output_dir = "DATA/VIDEOS/OUTPUTS"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"microsleep_detection_{timestamp}.mp4")
        
        # Initialize video writer
        fourcc = cv.VideoWriter_fourcc(*'mp4v')
        self.out = cv.VideoWriter(output_path, fourcc, self.fps, 
                                 (self.frame_width, self.frame_height))
        print(f"Recording video to: {output_path}")

    def _init_tracking_variables(self):
        """Initialize variables used for tracking blinks and microsleep events"""
        # Frame counters
        self.frame_number = 0
        self.blink_counter = 0
        self.microsleep_counter = 0
        
        # State tracking
        self.frame_counter = 0  # Count consecutive frames with closed eyes
        self.microsleep_frame_counter = 0  # Count consecutive frames in potential microsleep
        self.alert_state = self.ALERT_STATES['NORMAL']
        self.last_state = self.ALERT_STATES['NORMAL']
        self.state_stability = 0  # Counter for stable state detection
        
        # Data for analysis and plotting
        self.ear_values = deque(maxlen=180)  # Store last 180 EAR values (about 6 seconds at 30fps)
        self.smoothed_ear_values = deque(maxlen=180)  # Store smoothed EAR values
        self.frame_numbers = deque(maxlen=180)  # Corresponding frame numbers
        self.blink_frames = []  # Store frame numbers where blinks occurred
        self.microsleep_frames = []  # Store frame numbers where microsleep was detected
        
        # Calibration data
        self.calibration_ears = []
        self.calibration_complete = False
        self.calibration_frames = 60  # Use 60 frames for calibration
        self.adaptive_threshold = None
        
        # Timing data
        self.last_blink_time = time.time()
        self.blink_interval_times = deque(maxlen=20)  # Store last 20 blink intervals
        
        # Performance monitoring
        self.processing_times = deque(maxlen=30)  # Store recent frame processing times
        self.last_frame_time = None

    def _init_plot(self):
        """Initialize the matplotlib plot for EAR visualization"""
        plt.style.use('dark_background')
        plt.ioff()  # Turn off interactive mode
        
        # Create figure and axes
        self.fig, self.ax = plt.subplots(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        
        # Configure plot aesthetics
        self._configure_plot_aesthetics()
        
        # Initialize plot data structures
        self.EAR_curve = None
        self.smoothed_EAR_curve = None
        self.threshold_line = None
        self.adaptive_line = None
        self.microsleep_spans = []
        self.blink_markers = []
        
        # Initialize the plot
        self._init_plot_data()

    def _configure_plot_aesthetics(self):
        """Configure the aesthetic properties of the plot"""
        # Set background colors
        self.fig.patch.set_facecolor('#000000')
        self.ax.set_facecolor('#000000')
        
        # Configure axes with default limits
        self.ax.set_ylim(0.15, 0.4)  # Typical EAR range
        self.ax.set_xlim(0, 180)
        
        # Set labels and title
        self.ax.set_xlabel("Frame Number", color='white', fontsize=10)
        self.ax.set_ylabel("EAR", color='white', fontsize=10)
        self.ax.set_title("Real-Time Eye Aspect Ratio (EAR)", 
                         color='white', pad=10, fontsize=14, fontweight='bold')
        
        # Configure grid and spines
        self.ax.grid(True, color='#707b7c', linestyle='--', alpha=0.7)
        for spine in self.ax.spines.values():
            spine.set_color('white')
        
        # Configure ticks
        self.ax.tick_params(colors='white', which='both')

    def _init_plot_data(self):
        """Initialize the plot data and curves"""
        # Initial data
        x_vals = list(range(180))
        y_vals = [0.3] * 180  # Default value for visualization
        threshold_vals = [self.EAR_THRESHOLD] * 180
        
        # Create curves with explicit labels
        self.EAR_curve, = self.ax.plot(
            x_vals, 
            y_vals,
            color=self.COLORS['GREEN']['hex'],
            label="Eye Aspect Ratio",
            linewidth=1.5,
            alpha=0.7
        )
        
        self.smoothed_EAR_curve, = self.ax.plot(
            x_vals,
            y_vals,
            color=self.COLORS['BLUE']['hex'],
            label="Smoothed EAR",
            linewidth=2
        )
        
        self.threshold_line, = self.ax.plot(
            x_vals,
            threshold_vals,
            color=self.COLORS['RED']['hex'],
            label="Blink Threshold",
            linewidth=2,
            linestyle='--'
        )
        
        # Add adaptive threshold line if using calibration
        if self.adaptive_threshold:
            self.adaptive_line, = self.ax.plot(
                x_vals,
                [self.adaptive_threshold] * 180,
                color=self.COLORS['YELLOW']['hex'],
                label="Adaptive Threshold",
                linewidth=2,
                linestyle=':'
            )
            
        # Add legend
        handles = [self.EAR_curve, self.smoothed_EAR_curve, self.threshold_line]
        if self.adaptive_threshold:
            handles.append(self.adaptive_line)
            
        self.legend = self.ax.legend(
            handles=handles,
            loc='upper left',
            fontsize=8,
            facecolor='black',
            edgecolor='white',
            labelcolor='white',
            framealpha=0.8
        )
        
        # Draw the canvas
        self.fig.canvas.draw()

    def calibrate_threshold(self, ear):
        """
        Calibrate the adaptive threshold based on initial frames
        
        Args:
            ear (float): Current EAR value
        """
        if not self.calibration_complete:
            # Collect EAR values during calibration
            self.calibration_ears.append(ear)
            
            # Display calibration progress 
            progress = len(self.calibration_ears) / self.calibration_frames * 100
            
            # When calibration is complete
            if len(self.calibration_ears) >= self.calibration_frames:
                # Calculate adaptive threshold (mean - 2.5 * standard deviation)
                # Filter out potential outliers
                filtered_ears = np.array(self.calibration_ears)
                mean_ear = np.mean(filtered_ears)
                std_ear = np.std(filtered_ears)
                
                # Remove outliers (values more than 2 std from mean)
                filtered_ears = filtered_ears[abs(filtered_ears - mean_ear) < 2 * std_ear]
                
                # Recalculate with filtered values
                if len(filtered_ears) > 0:
                    mean_ear = np.mean(filtered_ears)
                    std_ear = np.std(filtered_ears)
                
                # Ensure we don't set an unreasonable threshold
                # More aggressive threshold calculation: mean - 1.8 * std
                calculated_threshold = mean_ear - 1.8 * std_ear
                safe_min = 0.15  # Minimum reasonable threshold
                safe_max = 0.28   # Maximum reasonable threshold
                
                self.adaptive_threshold = max(min(calculated_threshold, safe_max), safe_min)
                self.calibration_complete = True
                
                print(f"Calibration complete. Adaptive threshold: {self.adaptive_threshold:.4f}")
                
                # Update the plot with adaptive threshold
                if self.display_plot:
                    self.adaptive_line, = self.ax.plot(
                        list(range(180)),
                        [self.adaptive_threshold] * 180,
                        color=self.COLORS['YELLOW']['hex'],
                        label="Adaptive Threshold",
                        linewidth=2,
                        linestyle=':'
                    )
                    
                    # Update legend
                    handles = [self.EAR_curve, self.smoothed_EAR_curve, self.threshold_line, self.adaptive_line]
                    self.legend = self.ax.legend(
                        handles=handles,
                        loc='upper left',
                        fontsize=8,
                        facecolor='black',
                        edgecolor='white',
                        labelcolor='white',
                        framealpha=0.8
                    )
            
            return progress
        
        return 100  # Calibration already complete

    def _update_plot(self, ear, smoothed_ear):
        """
        Update the plot with new EAR values
        
        Args:
            ear (float): Current EAR value
            smoothed_ear (float): Smoothed EAR value
        """
        if not self.display_plot:
            return
            
        # Determine color based on alert state
        colors = {
            self.ALERT_STATES['NORMAL']: self.COLORS['GREEN']['hex'],
            self.ALERT_STATES['BLINK']: self.COLORS['BLUE']['hex'],
            self.ALERT_STATES['DROWSY']: self.COLORS['YELLOW']['hex'],
            self.ALERT_STATES['MICROSLEEP']: self.COLORS['RED']['hex']
        }
        
        color = colors[self.alert_state]
        
        # Update data
        self.EAR_curve.set_xdata(self.frame_numbers)
        self.EAR_curve.set_ydata(self.ear_values)
        self.EAR_curve.set_color(color)
        
        # Update smoothed EAR curve
        self.smoothed_EAR_curve.set_xdata(self.frame_numbers)
        self.smoothed_EAR_curve.set_ydata(self.smoothed_ear_values)
        
        # Update threshold line
        self.threshold_line.set_xdata(self.frame_numbers)
        self.threshold_line.set_ydata([self.EAR_THRESHOLD] * len(self.frame_numbers))
        
        # Update adaptive threshold line if it exists
        if self.adaptive_threshold and self.adaptive_line:
            self.adaptive_line.set_xdata(self.frame_numbers)
            self.adaptive_line.set_ydata([self.adaptive_threshold] * len(self.frame_numbers))
        
        # Update x-axis limits to slide with the data
        if len(self.frame_numbers) > 1:
            x_min = min(self.frame_numbers)
            x_max = max(self.frame_numbers)
            x_range = x_max - x_min
            
            # Ensure there's a margin and handle initial cases
            margin = max(5, int(x_range * 0.1))
            self.ax.set_xlim(x_min - margin, x_max + margin)
        
        # Clear previous microsleep spans
        for span in self.microsleep_spans:
            span.remove()
        self.microsleep_spans = []
        
        # Clear previous blink markers
        for marker in self.blink_markers:
            marker.remove()
        self.blink_markers = []
        
        # Add blink markers
        for frame in self.blink_frames:
            if frame in self.frame_numbers:
                marker = self.ax.plot([frame], [0.2], 'o', color='blue', markersize=6, alpha=0.7)[0]
                self.blink_markers.append(marker)
        
        # Highlight microsleep regions if any
        if self.microsleep_frames:
            for frame in self.microsleep_frames:
                if frame in self.frame_numbers:
                    span = self.ax.axvspan(frame-5, frame+5, color='red', alpha=0.3)
                    self.microsleep_spans.append(span)
        
        # Adjust y-axis limits based on observed EAR values
        if len(self.ear_values) > 0:
            ear_min = min(self.ear_values)
            ear_max = max(self.ear_values)
            margin = (ear_max - ear_min) * 0.1
            
            # Ensure reasonable limits
            y_min = max(0.1, ear_min - margin)
            y_max = min(0.5, ear_max + margin)
            
            # Ensure minimum range to prevent extreme zoom
            if y_max - y_min < 0.1:
                y_center = (y_min + y_max) / 2
                y_min = y_center - 0.05
                y_max = y_center + 0.05
                
            self.ax.set_ylim(y_min, y_max)
        
        # Redraw canvas
        self.fig.canvas.draw()

    def plot_to_image(self):
        """
        Convert the matplotlib plot to an OpenCV-compatible image
        
        Returns:
            np.ndarray: OpenCV image of the plot
        """
        if not self.display_plot:
            return None
            
        self.canvas.draw()
        
        buffer = self.canvas.buffer_rgba()
        img_array = np.asarray(buffer)
        
        # Convert RGBA to BGR (OpenCV format)
        img_rgb = cv.cvtColor(img_array, cv.COLOR_RGBA2RGB)
        img_bgr = cv.cvtColor(img_rgb, cv.COLOR_RGB2BGR)
        
        return img_bgr

    def process_frame(self, frame):
        """
        Process a single frame to detect eyes and analyze for microsleep
        
        Args:
            frame (np.ndarray): Input video frame
            
        Returns:
            tuple: Processed frame and EAR values
        """
        # Get face mesh landmarks
        frame, face_landmarks = self.generator.create_face_mesh(frame, draw=False)
        
        if not face_landmarks:
            # No face detected
            return frame, None, None
            
        # Calculate EAR using the eye analyzer
        right_ear, left_ear, avg_ear, smoothed_ear = self.eye_analyzer.calculate_ear(face_landmarks)
        
        # Determine the threshold to use
        threshold = self.adaptive_threshold if self.calibration_complete else self.EAR_THRESHOLD
        
        # Determine visualization color based on alert state
        colors = {
            self.ALERT_STATES['NORMAL']: self.COLORS['GREEN']['bgr'],
            self.ALERT_STATES['BLINK']: self.COLORS['BLUE']['bgr'],
            self.ALERT_STATES['DROWSY']: self.COLORS['YELLOW']['bgr'],
            self.ALERT_STATES['MICROSLEEP']: self.COLORS['RED']['bgr']
        }
        
        color = colors[self.alert_state]
        
        # Draw eye landmarks and status
        self._draw_frame_elements(frame, face_landmarks, avg_ear, smoothed_ear, threshold, color)
        
        return frame, avg_ear, smoothed_ear

    def _draw_frame_elements(self, frame, landmarks, ear, smoothed_ear, threshold, color):
        """
        Draw eye landmarks and status information on the frame
        
        Args:
            frame (np.ndarray): Input frame
            landmarks (dict): Facial landmarks
            ear (float): Eye aspect ratio
            smoothed_ear (float): Smoothed eye aspect ratio
            threshold (float): Current threshold for eye closure
            color (tuple): Color for visualization
        """
        # Draw eye landmarks
        for eye_points in [self.eye_analyzer.RIGHT_EYE, self.eye_analyzer.LEFT_EYE]:
            for loc in eye_points:
                if loc in landmarks:
                    cv.circle(frame, landmarks[loc], 1, color, cv.FILLED)
        
        # Draw attention rectangle around eyes
        DrawingUtils.draw_attention_rectangle(
            frame, landmarks, self.eye_analyzer.RIGHT_EYE + self.eye_analyzer.LEFT_EYE, 
            padding=10, color=color, thickness=2
        )
        
        # Draw EAR values
        DrawingUtils.draw_text_with_bg(
            frame, f"EAR: {ear:.4f}", (10, 30),
            font_scale=0.7, thickness=2,
            bg_color=color, text_color=(0, 0, 0)
        )
        
        DrawingUtils.draw_text_with_bg(
            frame, f"Smoothed: {smoothed_ear:.4f}", (10, 60),
            font_scale=0.7, thickness=2,
            bg_color=color, text_color=(0, 0, 0)
        )
        
        # Draw blink counter
        DrawingUtils.draw_text_with_bg(
            frame, f"Blinks: {self.blink_counter}", (10, 90),
            font_scale=0.7, thickness=2,
            bg_color=color, text_color=(0, 0, 0)
        )
        
        # Draw microsleep counter
        DrawingUtils.draw_text_with_bg(
            frame, f"Microsleeps: {self.microsleep_counter}", (10, 120),
            font_scale=0.7, thickness=2,
            bg_color=color, text_color=(0, 0, 0)
        )
        
        # Draw threshold
        DrawingUtils.draw_text_with_bg(
            frame, f"Threshold: {threshold:.4f}", (10, 150),
            font_scale=0.7, thickness=2,
            bg_color=color, text_color=(0, 0, 0)
        )
        
        # Draw alert state
        state_names = {v: k for k, v in self.ALERT_STATES.items()}
        state_text = state_names[self.alert_state]
        
        DrawingUtils.draw_text_with_bg(
            frame, f"State: {state_text}", (10, 180),
            font_scale=0.7, thickness=2,
            bg_color=color, text_color=(0, 0, 0)
        )
        
        # Draw FPS
        if self.processing_times and len(self.processing_times) > 0:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            fps = 1.0 / avg_time if avg_time > 0 else 0
            
            DrawingUtils.draw_text_with_bg(
                frame, f"FPS: {fps:.1f}", (frame.shape[1] - 100, 30),
                font_scale=0.7, thickness=2,
                bg_color=(100, 100, 100), text_color=(255, 255, 255)
            )
        
        # Draw microsleep alert
        if self.alert_state == self.ALERT_STATES['MICROSLEEP']:
            # Draw large warning text
            text = "MICROSLEEP DETECTED!"
            font_scale = 1.0
            thickness = 2
            
            # Get text size
            (text_width, text_height), baseline = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            
            # Calculate position for center of frame
            x = (frame.shape[1] - text_width) // 2
            y = frame.shape[0] - 50
            
            # Draw text with background
            cv.rectangle(frame, (x - 10, y - text_height - 10), (x + text_width + 10, y + 10), (0, 0, 255), cv.FILLED)
            cv.putText(frame, text, (x, y), cv.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
            
            # Add red border around frame
            cv.rectangle(frame, (0, 0), (frame.shape[1]-1, frame.shape[0]-1), (0, 0, 255), 10)
        
        # Draw calibration status if not complete
        if not self.calibration_complete:
            progress = len(self.calibration_ears) / self.calibration_frames * 100
            
            # Draw progress bar
            bar_width = 200
            filled_width = int(progress / 100 * bar_width)
            
            # Draw background
            cv.rectangle(frame, (10, frame.shape[0] - 50), (10 + bar_width, frame.shape[0] - 30), (0, 0, 0), cv.FILLED)
            cv.rectangle(frame, (10, frame.shape[0] - 50), (10 + bar_width, frame.shape[0] - 30), (255, 255, 255), 1)
            
            # Draw filled portion
            cv.rectangle(frame, (10, frame.shape[0] - 50), (10 + filled_width, frame.shape[0] - 30), (0, 255, 0), cv.FILLED)
            
            # Draw text
            cv.putText(frame, f"Calibrating: {progress:.1f}%", (10, frame.shape[0] - 60),
                      cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def _send_data_to_server(self, status_alert):
        """
        Send detection data to server and fallback to Ubidots if failed.
        """
        current_time = time.time()
        if current_time - self.last_data_sent_time < self.data_send_interval:
            return

        self.last_data_sent_time = current_time
        binary_status = "ON" if status_alert in ["BLINK", "DROWSY", "MICROSLEEP"] else "OFF"

        # Kirim sinyal ke ESP32 jika status "ON"
        if binary_status == "ON":
            self.send_serial_signal('B')

        # Payload utama
        payload = {
            "nama_sopir": self.driver_name,
            "timestamp": datetime.now().isoformat(),
            "armada": self.armada,
            "rute": self.rute,
            "status_alert": binary_status,
        }

        print(f"[{payload['timestamp']}] Sopir: {payload['nama_sopir']} | "
            f"Armada: {payload['armada']} | Rute: {payload['rute']} | Status: {payload['status_alert']}")

        if not self.server_url or self.server_url == "dummy_url":
            print("⚠️ Server URL tidak valid. Melewati pengiriman ke server.")
            self._send_to_ubidots(status_alert, payload)
            return

        try:
            response = requests.post(self.server_url, json=payload, timeout=3)
            if 200 <= response.status_code < 300:
                print(f"✅ Data berhasil dikirim ke server. Response: {response.text[:100]}...")
            else:
                print(f"❌ Gagal kirim ke server. Status: {response.status_code}")
                self._send_to_ubidots(status_alert, payload)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"❌ Tidak dapat menghubungi server: {e}")
            self._send_to_ubidots(status_alert, payload)
        except Exception as e:
            print(f"❌ Error saat mengirim ke server: {e}")
            self._send_to_ubidots(status_alert, payload)


    def _send_to_ubidots(self, status_alert, payload):
        """
        Fallback: Kirim data ke Ubidots jika server utama gagal.
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            ubidots_token = os.getenv("UBIDOTS_TOKEN")
            device_label = os.getenv("DEVICE_LABEL", "esp32-cam")

            if not ubidots_token:
                print("⚠️ Token Ubidots tidak ditemukan. Skipping upload.")
                return

            ubidots_payload = {
                "driver_name": payload.get("nama_sopir", "Unknown"),
                "armada": payload.get("armada", "Unknown"),
                "rute": payload.get("rute", "Unknown"),
                "timestamp": payload.get("timestamp", datetime.now().isoformat()),
                "status_alert": 1 if status_alert == "MICROSLEEP" else 0
            }

            headers = {
                "X-Auth-Token": ubidots_token,
                "Content-Type": "application/json"
            }

            url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{device_label}"
            response = requests.post(url, headers=headers, json=ubidots_payload, timeout=5)

            if 200 <= response.status_code < 300:
                print("✅ Data berhasil dikirim ke Ubidots.")
            else:
                print(f"❌ Gagal kirim ke Ubidots. Status: {response.status_code} | Response: {response.text[:100]}")

        except Exception as e:
            print(f"❌ Error saat mengirim ke Ubidots: {e}")


    def _update_blink_detection(self, ear, smoothed_ear):
        """
        Update blink detection based on EAR value
        
        Args:
            ear (float): Current EAR value
            smoothed_ear (float): Smoothed EAR value
        """
        # Store data for plotting
        self.ear_values.append(ear)
        self.smoothed_ear_values.append(smoothed_ear)
        self.frame_numbers.append(self.frame_number)
        
        # Use the adaptive threshold if calibration is complete
        threshold = self.adaptive_threshold if self.calibration_complete else self.EAR_THRESHOLD
        
        # Previous status for checking changes
        previous_state = self.alert_state
        
        # Microsleep detection logic
        if smoothed_ear < threshold:
            self.frame_counter += 1
            
            # If eyes have been closed for enough frames, consider it a blink
            if self.frame_counter == self.CONSEC_FRAMES:
                self.blink_counter += 1
                self.blink_frames.append(self.frame_number)
                
                # Calculate time since last blink
                current_time = time.time()
                blink_interval = current_time - self.last_blink_time
                self.last_blink_time = current_time
                
                # Store blink interval (used for microsleep detection)
                if blink_interval < 10:  # Ignore very long intervals (e.g., when starting)
                    self.blink_interval_times.append(blink_interval)
                
                # Set alert state to BLINK
                self.alert_state = self.ALERT_STATES['BLINK']
            
            # If eyes have been closed for a longer period, consider potential microsleep
            if self.frame_counter >= self.CONSEC_FRAMES:
                self.microsleep_frame_counter += 1
                
                # If microsleep criteria met, update state
                if self.microsleep_frame_counter >= self.MICROSLEEP_FRAMES:
                    # Check if this is actually microsleep using classifier
                    recent_ears = list(self.ear_values)[-30:]  # Get last 30 EAR values
                    
                    # Calculate microsleep duration in seconds
                    microsleep_duration = self.microsleep_frame_counter / self.fps
                    
                    # Only use classifier if we have enough data
                    if len(recent_ears) >= 10:
                        # Get microsleep prediction
                        is_microsleep = self.microsleep_classifier.predict(
                            recent_ears, 
                            list(self.blink_interval_times),
                            microsleep_duration
                        )
                        
                        # If classified as microsleep
                        if is_microsleep:
                            # First time we detect this microsleep
                            if self.alert_state != self.ALERT_STATES['MICROSLEEP']:
                                self.microsleep_counter += 1
                                self.microsleep_frames.append(self.frame_number)
                                
                                # Play alert sound if enabled
                                print("⚠️ MICROSLEEP detected!")
                                if self.enable_audio:
                                    self._play_alert()
                            
                            self.alert_state = self.ALERT_STATES['MICROSLEEP']
                        else:
                            self.alert_state = self.ALERT_STATES['DROWSY']
                    else:
                        # Not enough data for classification, but still consider drowsy
                        if self.microsleep_frame_counter >= self.MICROSLEEP_FRAMES * 1.5:
                            self.alert_state = self.ALERT_STATES['MICROSLEEP']
                            
                            # First time we detect this microsleep (fallback detection)
                            if self.last_state != self.ALERT_STATES['MICROSLEEP']:
                                self.microsleep_counter += 1
                                self.microsleep_frames.append(self.frame_number)
                                
                                # Play alert sound if enabled
                                if self.enable_audio:
                                    self._play_alert()
                        else:
                            self.alert_state = self.ALERT_STATES['DROWSY']
        else:
            # Eyes are open
            if self.frame_counter >= self.CONSEC_FRAMES:
                # Eyes were closed and now open
                # Reset counters
                self.frame_counter = 0
                self.microsleep_frame_counter = 0
                
                # Reset alert state to normal (with some state stability)
                if self.alert_state == self.ALERT_STATES['MICROSLEEP']:
                    # Need more frames to transition out of microsleep
                    self.state_stability += 1
                    if self.state_stability >= 5:  # Require 5 consecutive open frames
                        self.alert_state = self.ALERT_STATES['NORMAL']
                        self.state_stability = 0
                else:
                    self.alert_state = self.ALERT_STATES['NORMAL']
            else:
                # Eyes were open and still open
                self.frame_counter = 0
                self.microsleep_frame_counter = 0
                self.alert_state = self.ALERT_STATES['NORMAL']
        
        # Send data to server if state changed or periodically
        if self.alert_state != previous_state or time.time() - self.last_data_sent_time >= self.data_send_interval:
            # Convert alert state enum to string
            state_names = {v: k for k, v in self.ALERT_STATES.items()}
            status_alert = state_names[self.alert_state]
            
            # Send data to server
            self._send_data_to_server(status_alert)
        
        # Store last state for state transition detection
        self.last_state = self.alert_state
        
        # Increment frame number
        self.frame_number += 1

    def _play_alert(self):
        """Play an alert sound when microsleep is detected"""
        current_time = time.time()
        if current_time - self.last_alert_time >= self.alert_cooldown:
            self.last_alert_time = current_time

            if self.audio_thread is None or not self.audio_thread.is_alive():
                try:
                    import platform
                    system = platform.system()

                    if system == 'Windows':
                        # Windows - use winsound
                        self.audio_thread = threading.Thread(
                            target=lambda: winsound.Beep(1000, 1000)
                        )
                    if system == 'Windows':
                        import winsound
                        self.audio_thread = threading.Thread(
                            target=lambda: winsound.Beep(1000, 1000)
                        )
                    elif system == 'Darwin':  # macOS
                        self.audio_thread = threading.Thread(
                            target=lambda: os.system('afplay /System/Library/Sounds/Sosumi.aiff')
                        )
                    else:
                        print('\a')  # Console bell (Linux)
                        self.audio_thread = None

                    if self.audio_thread:
                        self.audio_thread.daemon = True
                        self.audio_thread.start()
                except Exception as e:
                    print(f"Error playing alert sound: {e}")
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(b'B')  # Kirim karakter 'B' ke ESP32
                print("📢 Sent 'B' to ESP32 for buzzer alert.")
            except Exception as e:
                print(f"❌ Failed to write to serial port: {e}")


    def run(self):
        """Main loop to continuously process video frames"""
        try:
            while self.cap.isOpened():
                # Record start time for FPS calculation
                start_time = time.time()
                
                # Read a frame
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Process the frame
                frame, ear, smoothed_ear = self.process_frame(frame)
                
                if ear is not None and smoothed_ear is not None:
                    # Perform calibration if needed
                    if not self.calibration_complete:
                        self.calibrate_threshold(ear)
                    
                    # Update blink detection
                    self._update_blink_detection(ear, smoothed_ear)
                    
                    # Update the plot
                    if self.display_plot:
                        self._update_plot(ear, smoothed_ear)
                        
                        # Convert plot to image
                        plot_img = self.plot_to_image()
                        
                        if plot_img is not None:
                            # Resize plot to match frame width
                            plot_height = int(plot_img.shape[0] * frame.shape[1] / plot_img.shape[1])
                            plot_img_resized = cv.resize(plot_img, (frame.shape[1], plot_height))
                            
                            # Stack images vertically
                            stacked_frame = cv.vconcat([frame, plot_img_resized])
                            
                            # Show resized output
                            display_img = cv.resize(stacked_frame, (0, 0), fx=0.8, fy=0.8)
                            cv.imshow('Microsleep Detection', display_img)
                        else:
                            cv.imshow('Microsleep Detection', frame)
                    else:
                        cv.imshow('Microsleep Detection', frame)
                else:
                    # No face detected
                    cv.putText(frame, "No face detected", (30, 30), 
                              cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv.imshow('Microsleep Detection', frame)
                
                # Save the frame if recording
                if self.save_video and self.out is not None:
                    self.out.write(frame)
                    
                # Calculate processing time for this frame
                end_time = time.time()
                process_time = end_time - start_time
                self.processing_times.append(process_time)
                
                # Use dynamic delay to maintain consistent frame rate
                # Only wait if processing was faster than frame rate
                target_frame_time = 1.0 / self.fps
                remaining_time = target_frame_time - process_time
                if remaining_time > 0:
                    wait_ms = int(remaining_time * 1000)
                    if cv.waitKey(wait_ms) & 0xFF == ord('q'):
                        break
                else:
                    # Processing is slower than frame rate, check for key press without waiting
                    if cv.waitKey(1) & 0xFF == ord('q'):
                        break
                    
        except Exception as e:
            print(f"Error in microsleep detection: {e}")
            import traceback
            traceback.print_exc()

    def release_resources(self):
        """Release video capture and writer resources"""
        if self.cap is not None:
            self.cap.release()
        
        if self.out is not None:
            self.out.release()
            
        # Close plot
        if self.display_plot and plt.fignum_exists(self.fig.number):
            plt.close(self.fig)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("🔌 Serial port closed.")

            
    def adjust_sensitivity(self, sensitivity):
        """
        Adjust the sensitivity of microsleep detection.
        
        Args:
            sensitivity (float): Value between 0.0 (least sensitive) and 1.0 (most sensitive)
        """
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        
        # Update classifier sensitivity
        self.microsleep_classifier.set_sensitivity(self.sensitivity)
        
        # Adjust other parameters based on sensitivity
        self.MICROSLEEP_FRAMES = int(20 - (self.sensitivity * 10))  # Range from 10 to 20
        
        print(f"Sensitivity adjusted to {self.sensitivity:.2f}, microsleep frames threshold: {self.MICROSLEEP_FRAMES}")