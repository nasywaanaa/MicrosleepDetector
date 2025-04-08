import argparse
import cv2
from microsleep_detector import MicrosleepDetector

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Realtime Microsleep Detection System")
    parser.add_argument("--threshold", type=float, default=0.21,
                        help="Initial EAR threshold for blink detection (default: 0.21)")
    parser.add_argument("--consec_frames", type=int, default=2,
                        help="Number of consecutive frames for blink detection (default: 2)")
    parser.add_argument("--microsleep_frames", type=int, default=15,
                        help="Number of consecutive frames for microsleep detection (default: 15)")
    parser.add_argument("--camera", type=int, default=0,
                        help="Camera device index (default: 0)")
    parser.add_argument("--record", action="store_true",
                        help="Record the detection session")
    parser.add_argument("--display_plot", action="store_true", default=True,
                        help="Display the EAR plot")
    parser.add_argument("--sensitivity", type=float, default=0.8,
                        help="Detection sensitivity (0.0-1.0, default: 0.8)")
    parser.add_argument("--audio", action="store_true", default=True,
                        help="Enable audio alerts")
    
    return parser.parse_args()

def main():
    """Main function to run the microsleep detection system"""
    # Parse arguments
    args = parse_arguments()
    
    print("\n========== Microsleep Detection System ==========")
    print(f"EAR Threshold: {args.threshold}")
    print(f"Consecutive Frames for Blink: {args.consec_frames}")
    print(f"Consecutive Frames for Microsleep: {args.microsleep_frames}")
    print(f"Camera: {args.camera}")
    print(f"Recording: {'Enabled' if args.record else 'Disabled'}")
    print(f"Display Plot: {'Enabled' if args.display_plot else 'Disabled'}")
    print(f"Audio Alerts: {'Enabled' if args.audio else 'Disabled'}")
    print(f"Sensitivity: {args.sensitivity}")
    print("================================================\n")
    
    print("Starting detection system...")
    print("Press 'q' to quit")
    print("During calibration, please maintain a neutral expression and keep your eyes open")
    
    # Initialize the microsleep detector
    detector = MicrosleepDetector(
        camera_id=args.camera,
        ear_threshold=args.threshold,
        consec_frames=args.consec_frames,
        microsleep_frames=args.microsleep_frames,
        save_video=args.record,
        display_plot=args.display_plot,
        enable_audio=args.audio,
        sensitivity=args.sensitivity
    )
    
    # Run the detector
    try:
        detector.run()
    except KeyboardInterrupt:
        print("\nStopping detection system (keyboard interrupt)...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        detector.release_resources()
        cv2.destroyAllWindows()
        print("Detection system stopped.")

if __name__ == "__main__":
    main()