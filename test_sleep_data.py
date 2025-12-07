import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from whoop_obsidian.models import WhoopConfig
from whoop_obsidian.whoop_client import WhoopClient

token = open(".whoop_api_token").read().strip()
config = WhoopConfig(base_url="https://api.prod.whoop.com/developer", metrics=["sleep_score"], timeout_seconds=30)
client = WhoopClient(config, token)

today = datetime.now()
start_iso = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
end_iso = (today.replace(hour=23, minute=59, second=59, microsecond=999999)).isoformat() + "Z"

sleep_data = client.get_sleep_collection(start=start_iso, end=end_iso, limit=5)
if sleep_data:
    sleep = sleep_data[0]
    print(f"Sleep ID: {sleep.id}")
    print(f"Start: {sleep.start}")
    print(f"End: {sleep.end}")
    print(f"Nap: {sleep.nap}")
    print(f"Duration (hours): {sleep.get_duration_hours()}")
    if sleep.score:
        print(f"\nScore data:")
        print(f"  Performance: {sleep.score.sleep_performance_percentage}%")
        print(f"  Efficiency: {sleep.score.sleep_efficiency_percentage}%")
        print(f"  Stage summary: {sleep.score.stage_summary}")
