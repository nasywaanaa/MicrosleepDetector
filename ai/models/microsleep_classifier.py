import numpy as np
from collections import deque
import time

class MicrosleepClassifier:
    """
    An improved classifier for detecting microsleep events based on eye aspect ratio patterns
    and blink interval characteristics.
    
    This model incorporates multiple detection methods and temporal analysis to
    identify potential microsleep episodes with higher accuracy.
    """
    
    def __init__(self):
        """Initialize the microsleep classifier with enhanced detection parameters."""
        # Normal blink parameters (typical ranges)
        self.normal_blink_duration_range = (0.1, 0.4)  # seconds
        self.normal_blink_ear_drop = 0.15  # typical EAR drop during normal blink
        
        # Microsleep parameters (more sensitive)
        self.microsleep_min_duration = 0.4  # minimum duration in seconds (reduced from 0.5)
        self.microsleep_max_duration = 30.0  # maximum duration in seconds
        
        # Microsleep detection sensitivity
        self.sensitivity = 0.7  # Higher values increase detection sensitivity (0.0-1.0)
        
        # Blink rate parameters
        self.normal_blink_rate_range = (8, 20)  # blinks per minute
        
        # Initialize history tracking
        self.blink_history = deque(maxlen=20)  # Store recent blink characteristics
        self.microsleep_history = deque(maxlen=10)  # Store recent microsleep events
        self.ear_history = deque(maxlen=120)  # Store recent EAR values for pattern analysis
        
        # Initialize time tracking
        self.last_blink_time = time.time()
        self.awake_duration = 0  # Time since last microsleep
        
        # Model performance stats
        self.detection_count = 0
        self.false_positive_estimate = 0
        
        # Frame rate estimation for time-based calculations
        self.estimated_fps = 30  # Default, will be updated based on actual data
        self.frame_times = deque(maxlen=30)  # Recent frame timestamps
        
        # Enhanced pattern recognition
        self.pattern_buffer = deque(maxlen=300)  # Store a longer history for pattern recognition
        self.detection_buffer = deque(maxlen=10)  # Recent detection results for temporal smoothing

    def update_fps_estimate(self):
        """Update the FPS estimate based on actual frame timing."""
        if len(self.frame_times) < 2:
            return
            
        # Calculate average time between frames
        diffs = [self.frame_times[i] - self.frame_times[i-1] for i in range(1, len(self.frame_times))]
        avg_diff = np.mean(diffs)
        if avg_diff > 0:
            self.estimated_fps = 1.0 / avg_diff

    def predict(self, ear_values, blink_intervals, closed_duration):
        """
        Predict whether a sequence of EAR values indicates a microsleep event.
        Enhanced version with multiple detection methods.
        
        Args:
            ear_values (list): Recent eye aspect ratio values
            blink_intervals (list): Recent time intervals between blinks (seconds)
            closed_duration (float): Duration of current eye closure (seconds)
            
        Returns:
            bool: True if microsleep is detected, False otherwise
        """
        # Record timestamp for FPS estimation
        current_time = time.time()
        self.frame_times.append(current_time)
        self.update_fps_estimate()
        
        # Add current EAR to history
        if ear_values and len(ear_values) > 0:
            self.ear_history.append(ear_values[-1])
            self.pattern_buffer.append(ear_values[-1])
        
        # Check if we have enough data to make a prediction
        if len(ear_values) < 5:
            return False
            
        # Apply multiple detection methods and combine results
        methods_results = []
        
        # Method 1: Duration-based detection
        duration_result = self._detect_by_duration(closed_duration)
        methods_results.append(duration_result)
        
        # Method 2: Pattern-based detection
        pattern_result = self._detect_by_pattern(ear_values)
        methods_results.append(pattern_result)
        
        # Method 3: Blink rate analysis
        blink_rate_result = False
        if blink_intervals and len(blink_intervals) >= 3:
            blink_rate_result = self._detect_by_blink_rate(blink_intervals)
        methods_results.append(blink_rate_result)
        
        # Method 4: PERCLOS-like metric
        perclos_result = self._detect_by_perclos(ear_values)
        methods_results.append(perclos_result)
        
        # Method 5: Wavelet-based detection for oscillatory patterns
        wavelet_result = self._detect_by_wavelet(list(self.pattern_buffer))
        methods_results.append(wavelet_result)
        
        # Combine results with weights based on reliability
        method_weights = [0.35, 0.25, 0.15, 0.15, 0.1]  # Duration, Pattern, Blink rate, PERCLOS, Wavelet
        weighted_score = sum(r * w for r, w in zip(methods_results, method_weights))
        
        # Apply sensitivity adjustment
        detection_threshold = 0.5 - (self.sensitivity * 0.3)  # Higher sensitivity = lower threshold
        is_microsleep = weighted_score >= detection_threshold
        
        # Apply temporal smoothing to reduce false positives
        self.detection_buffer.append(is_microsleep)
        smoothed_result = sum(self.detection_buffer) >= (len(self.detection_buffer) * 0.6)
        
        # 5. Update history
        if smoothed_result:
            self.microsleep_history.append({
                'timestamp': current_time,
                'duration': closed_duration,
                'ear_min': min(ear_values[-10:]) if ear_values else None,
                'confidence': weighted_score
            })
            self.detection_count += 1
        
        return smoothed_result

    def _detect_by_duration(self, closed_duration):
        """
        Detect microsleep based on eye closure duration.
        
        Args:
            closed_duration (float): Duration of current eye closure in seconds
            
        Returns:
            float: Score between 0.0 and 1.0 indicating microsleep probability
        """
        # Too short to be microsleep
        if closed_duration < self.microsleep_min_duration:
            return 0.0
            
        # Too long, likely a different issue or camera problem
        if closed_duration > self.microsleep_max_duration:
            return 0.0
            
        # Calculate microsleep probability based on duration
        # Peak probability around 2-3 seconds
        if closed_duration < 0.8:
            # Rapidly increasing probability from min_duration to 0.8s
            score = (closed_duration - self.microsleep_min_duration) / (0.8 - self.microsleep_min_duration)
            return max(0.0, min(0.8, score))
        elif closed_duration < 3.0:
            # Highest probability between 0.8s and 3.0s
            return 1.0
        else:
            # Gradually decreasing probability for very long closures
            # (might be other issues than microsleep)
            score = 1.0 - ((closed_duration - 3.0) / 27.0)
            return max(0.1, min(1.0, score))

    def _detect_by_pattern(self, ear_values):
        """
        Detect microsleep based on patterns in EAR values.
        
        Args:
            ear_values (list): Recent eye aspect ratio values
            
        Returns:
            float: Score between 0.0 and 1.0 indicating microsleep probability
        """
        if len(ear_values) < 10:
            return 0.0
            
        # Get statistics on recent EAR values
        ear_mean = np.mean(ear_values)
        ear_std = np.std(ear_values)
        ear_min = np.min(ear_values)
        ear_max = np.max(ear_values)
        
        # Calculate rate of change
        ear_diffs = np.diff(ear_values)
        
        # Criteria for microsleep pattern:
        # 1. Low minimum EAR (eyes closed)
        min_ear_score = 1.0 - (ear_min / 0.25)  # 0.0 -> 1.0, 0.25 -> 0.0
        min_ear_score = max(0.0, min(1.0, min_ear_score))
        
        # 2. Low variation in EAR during closure (stable closure, not fluctuating)
        stability_score = 1.0 - min(1.0, ear_std * 10)
        
        # 3. Rapid closure pattern
        if len(ear_diffs) >= 5:
            closure_diff = np.min(ear_diffs)
            closure_score = min(1.0, abs(closure_diff) * 10)
        else:
            closure_score = 0.0
        
        # Combine scores with weights
        pattern_score = (min_ear_score * 0.6) + (stability_score * 0.3) + (closure_score * 0.1)
        
        return pattern_score

    def _detect_by_blink_rate(self, blink_intervals):
        """
        Detect microsleep based on blink rate changes.
        
        Args:
            blink_intervals (list): Recent intervals between blinks (seconds)
            
        Returns:
            float: Score between 0.0 and 1.0 indicating microsleep probability
        """
        # Calculate blink rate (blinks per minute)
        mean_interval = np.mean(blink_intervals)
        if mean_interval > 0:
            blink_rate = 60.0 / mean_interval
        else:
            blink_rate = 0
        
        # Calculate blink rate score
        # Outside normal range (8-20 blinks/min) indicates potential fatigue
        if blink_rate < 8:
            # Slower blink rate often precedes microsleep
            rate_score = (8 - blink_rate) / 8
            rate_score = min(1.0, rate_score)
        elif blink_rate > 20:
            # More rapid blinking can also indicate fatigue
            rate_score = (blink_rate - 20) / 20
            rate_score = min(0.7, rate_score)  # Cap at 0.7 as high rate is less predictive than low rate
        else:
            # Normal blink rate
            rate_score = 0.0
        
        # Check for increasing trend in intervals (slowing blink rate)
        if len(blink_intervals) >= 6:
            early_intervals = blink_intervals[:3]
            late_intervals = blink_intervals[-3:]
            
            interval_change = np.mean(late_intervals) - np.mean(early_intervals)
            
            if interval_change > 0:
                # Increasing intervals = slowing blink rate = higher microsleep chance
                trend_score = min(1.0, interval_change)
            else:
                trend_score = 0.0
        else:
            trend_score = 0.0
        
        # Calculate final score
        final_score = max(rate_score, trend_score)
        
        return final_score

    def _detect_by_perclos(self, ear_values, threshold=0.2, window_size=90):
        """
        Detect microsleep using a PERCLOS-like metric.
        
        Args:
            ear_values (list): Recent eye aspect ratio values
            threshold (float): Threshold for eye closure
            window_size (int): Window size in frames
            
        Returns:
            float: Score between 0.0 and 1.0 indicating microsleep probability
        """
        if len(ear_values) < window_size / 2:
            return 0.0
            
        # Use most recent values
        values = ear_values[-min(len(ear_values), window_size):]
        
        # Calculate percentage of frames with eyes closed
        closed_percentage = sum(1 for ear in values if ear < threshold) / len(values)
        
        # PERCLOS score
        # Over 80% = very likely microsleep
        # 40-80% = possible microsleep
        # Below 40% = unlikely microsleep
        if closed_percentage > 0.8:
            return 1.0
        elif closed_percentage > 0.4:
            # Linear increase from 0.0 at 40% to 1.0 at 80%
            return (closed_percentage - 0.4) / 0.4
        else:
            return 0.0

    def _detect_by_wavelet(self, ear_values, min_oscillations=3):
        """
        Detect microsleep by looking for oscillatory patterns in EAR.
        
        When fatigue sets in, people often experience oscillatory eye movements
        as they struggle to keep eyes open, creating a characteristic pattern.
        
        Args:
            ear_values (list): Recent eye aspect ratio values
            min_oscillations (int): Minimum oscillations to detect
            
        Returns:
            float: Score between 0.0 and 1.0 indicating microsleep probability
        """
        if len(ear_values) < 30:
            return 0.0
        
        # Use the most recent 90 frames (about 3 seconds at 30fps)
        values = ear_values[-min(len(ear_values), 90):]
        
        # Detect oscillation pattern (alternating increasing/decreasing)
        diffs = np.diff(values)
        sign_changes = np.sum(np.diff(np.signbit(diffs)) != 0)
        
        # Calculate oscillation score
        oscillation_score = min(1.0, sign_changes / (2 * min_oscillations))
        
        # Require evidence of overall decreasing trend
        if len(values) >= 30:
            start_mean = np.mean(values[:10])
            end_mean = np.mean(values[-10:])
            
            decreasing_trend = start_mean > end_mean
            trend_magnitude = min(1.0, (start_mean - end_mean) * 5)
            
            if decreasing_trend and trend_magnitude > 0.2:
                # Boost oscillation score if there's a decreasing trend
                oscillation_score *= (1 + trend_magnitude)
                
        return min(1.0, oscillation_score)

    def reset(self):
        """Reset the classifier state for a new session."""
        self.blink_history.clear()
        self.microsleep_history.clear()
        self.ear_history.clear()
        self.pattern_buffer.clear()
        self.detection_buffer.clear()
        self.frame_times.clear()
        
        self.last_blink_time = time.time()
        self.awake_duration = 0
        self.detection_count = 0
        self.false_positive_estimate = 0
        
    def get_statistics(self):
        """Get current statistics about microsleep detection."""
        stats = {
            'detection_count': self.detection_count,
            'false_positive_estimate': self.false_positive_estimate,
        }
        
        # Calculate average duration if we have history
        if self.microsleep_history:
            durations = [event['duration'] for event in self.microsleep_history]
            stats['avg_duration'] = np.mean(durations)
            stats['max_duration'] = np.max(durations)
            
            # Calculate confidence in detections
            confidences = [event.get('confidence', 0.5) for event in self.microsleep_history]
            stats['avg_confidence'] = np.mean(confidences)
        
        # Calculate time pattern if we have multiple events
        if len(self.microsleep_history) >= 2:
            times = [event['timestamp'] for event in self.microsleep_history]
            intervals = np.diff(times)
            stats['avg_interval'] = np.mean(intervals)
            
        # Calculate FPS
        if len(self.frame_times) >= 2:
            stats['estimated_fps'] = self.estimated_fps
            
        return stats
        
    def set_sensitivity(self, sensitivity):
        """
        Set the sensitivity of the microsleep detector.
        
        Args:
            sensitivity (float): Value between 0.0 (least sensitive) and 1.0 (most sensitive)
        """
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        
        # Adjust parameters based on sensitivity
        self.microsleep_min_duration = 0.5 - (self.sensitivity * 0.2)  # 0.3s at highest sensitivity