import numpy as np

class EyeAspectRatioAnalyzer:
    """
    A class to analyze eye aspect ratio (EAR) using facial landmarks
    for blink and microsleep detection with improved accuracy.
    """
    
    # Define facial landmark indices for eyes using MediaPipe FaceMesh indices
    # Main eye landmarks (full eye contour)
    RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
    LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    
    # Points specifically for EAR calculation
    # These correspond to the vertical and horizontal points used in the EAR formula
    RIGHT_EYE_EAR = [33, 159, 158, 133, 153, 145]  # Top, bottom, and side points
    LEFT_EYE_EAR = [362, 386, 385, 263, 374, 380]  # Top, bottom, and side points

    def __init__(self):
        """Initialize the EyeAspectRatioAnalyzer with enhanced detection parameters."""
        # Store baseline EAR values for adaptive thresholding
        self.baseline_ear_values = []
        self.baseline_computed = False
        self.baseline_ear = None
        self.baseline_std = None
        
        # Smoothing parameters for filtering noise
        self.smoothing_window = 3  # Number of frames to average for smoothing
        self.ear_history = []  # Store recent EAR values for smoothing
        
        # Enhanced detection parameters
        self.min_blink_frames = 2  # Minimum frames for a valid blink
        self.max_blink_frames = 7  # Maximum frames for a normal blink (beyond this might be microsleep)
        
        # Adaptive threshold parameters
        self.threshold_ratio = 0.75  # Fraction of baseline used as threshold
        self.threshold_min = 0.15    # Minimum threshold to prevent detection issues
        self.threshold_max = 0.3     # Maximum threshold

    def calculate_ear(self, landmarks):
        """
        Calculate the eye aspect ratio for both eyes and the average with improved accuracy.
        
        Args:
            landmarks (dict): Dictionary of facial landmarks with coordinate values
            
        Returns:
            tuple: (right_ear, left_ear, average_ear, smoothed_ear)
        """
        # Check if we have all required landmarks
        if not all(p in landmarks for p in self.RIGHT_EYE_EAR + self.LEFT_EYE_EAR):
            return None, None, None, None
            
        # Calculate EAR for right eye
        right_ear = self._calculate_single_ear(self.RIGHT_EYE_EAR, landmarks)
        
        # Calculate EAR for left eye
        left_ear = self._calculate_single_ear(self.LEFT_EYE_EAR, landmarks)
        
        # Calculate average EAR
        avg_ear = (right_ear + left_ear) / 2.0
        
        # Apply smoothing to reduce noise
        self.ear_history.append(avg_ear)
        if len(self.ear_history) > self.smoothing_window:
            self.ear_history.pop(0)
        
        # Simple moving average smoothing
        smoothed_ear = sum(self.ear_history) / len(self.ear_history)
        
        # Update baseline if needed
        self._update_baseline(smoothed_ear)
        
        return right_ear, left_ear, avg_ear, smoothed_ear

    def _calculate_single_ear(self, eye_landmarks, landmarks):
        """
        Calculate EAR for a single eye with improved accuracy.
        
        Args:
            eye_landmarks (list): Indices of landmarks for one eye
            landmarks (dict): Dictionary of facial landmarks with coordinate values
            
        Returns:
            float: Calculated eye aspect ratio
        """
        # Get landmark coordinates
        p1 = np.array(landmarks[eye_landmarks[0]])
        p2 = np.array(landmarks[eye_landmarks[1]])
        p3 = np.array(landmarks[eye_landmarks[2]])
        p4 = np.array(landmarks[eye_landmarks[3]])
        p5 = np.array(landmarks[eye_landmarks[4]])
        p6 = np.array(landmarks[eye_landmarks[5]])
        
        # Calculate euclidean distances
        A = np.linalg.norm(p2 - p6)  # Vertical distance 1
        B = np.linalg.norm(p3 - p5)  # Vertical distance 2
        C = np.linalg.norm(p1 - p4)  # Horizontal distance
        
        # Avoid division by zero
        if C == 0:
            return 0.0
        
        # Calculate EAR with additional weighting to improve sensitivity
        # We put slightly more emphasis on the smaller of the two vertical distances
        # to make the detection more sensitive to eye closure
        min_vertical = min(A, B)
        max_vertical = max(A, B)
        
        # Weighted EAR calculation gives more weight to the smaller distance
        # This makes it more sensitive to partial blinks
        weighted_vertical = (min_vertical * 0.6) + (max_vertical * 0.4)
        ear = weighted_vertical / C
        
        return ear

    def _update_baseline(self, ear):
        """
        Update the baseline EAR value used for adaptive thresholding.
        
        Args:
            ear (float): Current smoothed EAR value
        """
        # Only collect baseline when eyes are likely open (above typical threshold)
        if ear > 0.2:
            # Collect values for baseline
            if len(self.baseline_ear_values) < 50 and not self.baseline_computed:
                self.baseline_ear_values.append(ear)
            
            # Compute baseline once we have enough samples
            if len(self.baseline_ear_values) >= 50 and not self.baseline_computed:
                # Remove outliers (values more than 2 std from mean)
                mean_ear = np.mean(self.baseline_ear_values)
                std_ear = np.std(self.baseline_ear_values)
                
                filtered_values = [e for e in self.baseline_ear_values 
                                  if abs(e - mean_ear) < 2 * std_ear]
                
                self.baseline_ear = np.mean(filtered_values)
                self.baseline_std = np.std(filtered_values)
                self.baseline_computed = True
        
        # Recalibrate if current EAR is significantly higher than baseline
        # This handles cases where the initial baseline might have been too low
        if self.baseline_computed and ear > (self.baseline_ear * 1.2) and ear > 0.25:
            self.baseline_ear = (self.baseline_ear * 0.8) + (ear * 0.2)  # Gradual update

    def get_adaptive_threshold(self):
        """
        Get the adaptive threshold based on baseline EAR.
        
        Returns:
            float: Adaptive threshold for blink detection
        """
        if not self.baseline_computed or self.baseline_ear is None:
            return 0.2  # Default if no baseline is available
        
        # Calculate threshold as a percentage of baseline
        threshold = self.baseline_ear * self.threshold_ratio
        
        # Ensure threshold is within reasonable bounds
        threshold = max(min(threshold, self.threshold_max), self.threshold_min)
        
        return threshold

    def detect_blinks(self, ear_values, threshold=None):
        """
        Enhanced blink detection algorithm with improved accuracy.
        
        This method detects blinks by analyzing a sequence of EAR values,
        with special handling for partial blinks and rapid blinks.
        
        Args:
            ear_values (list): Sequence of EAR values
            threshold (float): Threshold for eye closure, or None to use adaptive threshold
            
        Returns:
            list: Indices where blinks were detected
        """
        if not ear_values:
            return []
            
        # Use adaptive threshold if available, otherwise use provided threshold
        if threshold is None:
            threshold = self.get_adaptive_threshold()
        
        blink_indices = []
        below_threshold_count = 0
        potential_blink_start = None
        
        # First pass: detect intervals where EAR is below threshold
        for i, ear in enumerate(ear_values):
            if ear < threshold:
                # Start of potential blink
                if below_threshold_count == 0:
                    potential_blink_start = i
                
                below_threshold_count += 1
            else:
                # End of potential blink
                if below_threshold_count >= self.min_blink_frames and below_threshold_count <= self.max_blink_frames:
                    # Valid blink detected
                    blink_center = potential_blink_start + below_threshold_count // 2
                    blink_indices.append(blink_center)
                
                below_threshold_count = 0
                potential_blink_start = None
        
        # Check if we ended with an unfinished blink
        if below_threshold_count >= self.min_blink_frames and below_threshold_count <= self.max_blink_frames:
            blink_center = potential_blink_start + below_threshold_count // 2
            blink_indices.append(blink_center)
        
        # Second pass: look for rapid blinks that might have been missed
        # This looks for significant drops in EAR even if they don't go below threshold
        if len(ear_values) > 3:
            for i in range(1, len(ear_values) - 1):
                # Skip points already identified as blinks
                if i in blink_indices or i-1 in blink_indices or i+1 in blink_indices:
                    continue
                
                # Look for local minimum with significant drop
                if (ear_values[i] < ear_values[i-1] and 
                    ear_values[i] < ear_values[i+1] and
                    ear_values[i] < (self.baseline_ear * 0.85) and
                    (ear_values[i-1] - ear_values[i]) > (self.baseline_std * 1.5)):
                    
                    blink_indices.append(i)
        
        return blink_indices

    def calculate_perclos(self, ear_values, threshold=None, window_size=900):
        """
        Calculate PERCLOS (PERcentage of eye CLOSure) with improved accuracy.
        
        Args:
            ear_values (list): Sequence of EAR values
            threshold (float): Threshold for eye closure, or None to use adaptive threshold
            window_size (int): Number of frames to consider
            
        Returns:
            float: PERCLOS value (0-1 range)
        """
        # Use adaptive threshold if available, otherwise use provided threshold
        if threshold is None:
            threshold = self.get_adaptive_threshold()
            
        # Use only the most recent frames if we have more than window_size
        if len(ear_values) > window_size:
            ear_values = ear_values[-window_size:]
        
        # Count frames where eyes are below threshold
        closed_frames = sum(1 for ear in ear_values if ear < threshold)
        
        # Calculate percentage
        perclos = closed_frames / len(ear_values) if ear_values else 0
        
        return perclos

    def is_microsleep_candidate(self, ear_values, threshold=None, min_frames=15):
        """
        Determine if a sequence of EAR values indicates a potential microsleep.
        
        Args:
            ear_values (list): Sequence of EAR values
            threshold (float): Threshold for eye closure, or None to use adaptive threshold
            min_frames (int): Minimum consecutive frames for microsleep
            
        Returns:
            bool: True if pattern indicates microsleep, False otherwise
        """
        if not ear_values or len(ear_values) < min_frames:
            return False
            
        # Use adaptive threshold if available, otherwise use provided threshold
        if threshold is None:
            threshold = self.get_adaptive_threshold()
            
        # Count consecutive frames below threshold
        max_consecutive = 0
        current_consecutive = 0
        
        for ear in ear_values:
            if ear < threshold:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
                
        # Check if max consecutive frames exceeds minimum for microsleep
        return max_consecutive >= min_frames