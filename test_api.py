"""Quick script to test Whoop API and show data."""

import os
import sys
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from whoop_obsidian.models import WhoopConfig
from whoop_obsidian.whoop_client import WhoopClient


def main():
    """Test Whoop API and display data."""
    # Get token from environment
    token = os.environ.get("WHOOP_API_TOKEN")
    if not token:
        print("❌ WHOOP_API_TOKEN not set")
        print("\nTo get a token, run:")
        print("  uv run python -m whoop_obsidian.auth_helper")
        print("\nThen export it:")
        print("  export WHOOP_API_TOKEN='your_token'")
        return 1

    print("=" * 70)
    print("WHOOP API Data Test")
    print("=" * 70)
    print(f"\nToken: {token[:20]}...{token[-10:]}")
    print(f"Testing API at: https://api.prod.whoop.com/developer")

    # Create config
    config = WhoopConfig(
        base_url="https://api.prod.whoop.com/developer",
        metrics=["sleep_score", "recovery_score", "strain_score"],
        timeout_seconds=30,
    )

    # Create client
    client = WhoopClient(config, token)

    # Calculate date range
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    start_iso = week_ago.strftime("%Y-%m-%dT00:00:00Z")
    end_iso = today.strftime("%Y-%m-%dT23:59:59Z")

    print(f"\nFetching data from {week_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
    print("-" * 70)

    try:
        # Test 1: Sleep data
        print("\n📊 SLEEP DATA")
        print("-" * 70)
        sleep_data = client.get_sleep_collection(start=start_iso, end=end_iso, limit=5)
        print(f"Found {len(sleep_data)} sleep records")

        for i, sleep in enumerate(sleep_data[:3], 1):
            print(f"\n  Sleep #{i}:")
            print(f"    ID: {sleep.id}")
            print(f"    Start: {sleep.start}")
            print(f"    End: {sleep.end}")
            print(f"    Duration: {sleep.get_duration_hours():.1f} hours" if sleep.get_duration_hours() else "    Duration: N/A")
            print(f"    Nap: {sleep.nap}")
            print(f"    State: {sleep.score_state}")
            if sleep.score:
                print(f"    Performance: {sleep.score.sleep_performance_percentage}%")
                print(f"    Efficiency: {sleep.score.sleep_efficiency_percentage}%")

        # Test 2: Recovery data
        print("\n\n💪 RECOVERY DATA")
        print("-" * 70)
        recovery_data = client.get_recovery_collection(
            start=start_iso, end=end_iso, limit=5
        )
        print(f"Found {len(recovery_data)} recovery records")

        for i, recovery in enumerate(recovery_data[:3], 1):
            print(f"\n  Recovery #{i}:")
            print(f"    Cycle ID: {recovery.cycle_id}")
            print(f"    Sleep ID: {recovery.sleep_id}")
            print(f"    State: {recovery.score_state}")
            if recovery.score:
                print(f"    Recovery Score: {recovery.score.recovery_score}")
                print(f"    HRV: {recovery.score.hrv_rmssd_milli} ms")
                print(f"    RHR: {recovery.score.resting_heart_rate} bpm")
                print(f"    SpO2: {recovery.score.spo2_percentage}%")

        # Test 3: Cycle data (strain)
        print("\n\n🔥 CYCLE DATA (Strain)")
        print("-" * 70)
        cycle_data = client.get_cycle_collection(start=start_iso, end=end_iso, limit=5)
        print(f"Found {len(cycle_data)} cycle records")

        for i, cycle in enumerate(cycle_data[:3], 1):
            print(f"\n  Cycle #{i}:")
            print(f"    ID: {cycle.id}")
            print(f"    Start: {cycle.start}")
            print(f"    End: {cycle.end}")
            print(f"    State: {cycle.score_state}")
            if cycle.score:
                print(f"    Strain: {cycle.score.strain}")
                print(f"    Avg HR: {cycle.score.average_heart_rate} bpm")
                print(f"    Max HR: {cycle.score.max_heart_rate} bpm")
                print(f"    Kilojoules: {cycle.score.kilojoule}")

        # Test 4: Today's metrics
        print("\n\n📅 TODAY'S METRICS")
        print("-" * 70)
        metrics = client.fetch_today_metrics()
        print(f"  Sleep Score: {metrics.sleep_score or 'N/A'}")
        print(f"  Sleep Duration: {metrics.sleep_duration:.1f} hours" if metrics.sleep_duration else "  Sleep Duration: N/A")
        print(f"  Recovery Score: {metrics.recovery_score or 'N/A'}")
        print(f"  Strain Score: {metrics.strain_score or 'N/A'}")
        print(f"  HRV: {metrics.hrv or 'N/A'} ms")

        print("\n" + "=" * 70)
        print("✅ API Test Complete!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
