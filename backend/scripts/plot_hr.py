"""Create HR plot for the most recent activity in the database."""

import os
import matplotlib.pyplot as plt
from datetime import datetime
from app.core.database import SessionLocal
from app.models.models import Activity, HeartRateData
from app.clients.garmin import GarminClient

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def fetch_and_store_hr_data(activity_id):
    """Fetch heart rate data from Garmin and store in database."""
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        print("GARMIN_EMAIL and GARMIN_PASSWORD not set")
        return
    
    try:
        client = GarminClient(email, password)
        activity_detail = client.get_activity_details(activity_id)
        
        # Extract heart rate data from activityDetailMetrics
        # Based on actual data structure: index 0 = timestamp, index 3 = heart rate, index 4 = temperature
        if "activityDetailMetrics" in activity_detail:
            metrics_list = activity_detail["activityDetailMetrics"]
            print(f"Found {len(metrics_list)} metric entries")
            
            hr_data = []
            for metric_entry in metrics_list:
                if "metrics" in metric_entry:
                    metrics = metric_entry["metrics"]
                    # Actual array structure: [timestamp, ?, ?, heartRate, temperature, ?, ?, ?]
                    if len(metrics) >= 4:
                        timestamp_ms = metrics[0]
                        heart_rate = metrics[3]
                        
                        if heart_rate is not None and timestamp_ms is not None:
                            # Filter out unrealistic HR values
                            if 30 <= heart_rate <= 220:
                                hr_data.append({
                                    "timestamp": datetime.fromtimestamp(timestamp_ms / 1000),
                                    "value": heart_rate
                                })
            
            if not hr_data:
                print("No valid HR data found in metrics")
                return
            
            print(f"Fetched {len(hr_data)} HR data points from Garmin (after filtering)")
            
            # Store in database
            db = SessionLocal()
            try:
                # Clear existing HR data for this activity
                db.query(HeartRateData).filter(
                    HeartRateData.activity_id == activity_id
                ).delete()
                
                # Insert new HR data
                for point in hr_data:
                    hr_record = HeartRateData(
                        activity_id=activity_id,
                        timestamp=point["timestamp"],
                        heart_rate=point["value"]
                    )
                    db.add(hr_record)
                
                db.commit()
                print(f"Stored {len(hr_data)} HR data points in database")
            finally:
                db.close()
            return
        
        print("No activityDetailMetrics found in Garmin activity details")
    except Exception as e:
        print(f"Error fetching HR data from Garmin: {e}")

def plot_most_recent_activity_hr():
    """Create a heart rate plot for the most recent activity."""
    db = SessionLocal()
    
    try:
        # Get the most recent activity
        activity = db.query(Activity).order_by(Activity.start_time.desc()).first()
        
        if not activity:
            print("No activities found in database")
            return
        
        print(f"Most recent activity:")
        print(f"  ID: {activity.id}")
        print(f"  Type: {activity.activity_type}")
        print(f"  Date: {activity.start_time}")
        print(f"  Duration: {activity.duration_seconds / 60:.1f} minutes")
        
        # Get heart rate data
        hr_data = db.query(HeartRateData).filter(
            HeartRateData.activity_id == activity.id
        ).order_by(HeartRateData.timestamp).all()
        
        if not hr_data:
            print("No heart rate data found in database")
            print("Fetching from Garmin...")
            db.close()
            fetch_and_store_hr_data(activity.id)
            
            # Re-open database and fetch again
            db = SessionLocal()
            hr_data = db.query(HeartRateData).filter(
                HeartRateData.activity_id == activity.id
            ).order_by(HeartRateData.timestamp).all()
            
            if not hr_data:
                print("Still no heart rate data available")
                return
        
        print(f"  HR data points: {len(hr_data)}")
        
        # Extract timestamps and heart rates
        timestamps = [data.timestamp for data in hr_data]
        heart_rates = [data.heart_rate for data in hr_data]
        
        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, heart_rates, linewidth=2)
        plt.xlabel('Time')
        plt.ylabel('Heart Rate (bpm)')
        plt.title(f'Heart Rate - {activity.activity_type} on {activity.start_time.strftime("%Y-%m-%d %H:%M")}')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot
        output_file = f"hr_plot_{activity.id}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved to: {output_file}")
        
        # Show statistics
        avg_hr = sum(heart_rates) / len(heart_rates)
        max_hr = max(heart_rates)
        min_hr = min(heart_rates)
        print(f"\nHR Statistics:")
        print(f"  Average: {avg_hr:.1f} bpm")
        print(f"  Max: {max_hr} bpm")
        print(f"  Min: {min_hr} bpm")
        
    finally:
        db.close()

if __name__ == "__main__":
    plot_most_recent_activity_hr()
