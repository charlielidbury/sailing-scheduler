#!/usr/bin/env python3
"""Generate a schedule for 23 competitors with 90 races (3 sit-outs per round)."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Must configure BEFORE any other sailing_scheduler imports
import sailing_scheduler.models as models
models.NUM_COMPETITORS = 23
models.NUM_RACES = 90
# 9 rounds total, 3 sit-outs per round = 27 total sit-outs
# 27 ÷ 23 = 1.17 → some sit out once (16 races), some twice (14 races)
models.RACES_PER_COMPETITOR = 16  # Max (sits out once)
models.MIN_RACES_PER_COMPETITOR = 14  # Min (sits out twice)
models.COMPETITORS_PER_ROUND = 20  # 10 positions per boat × 2 boats
models.POSITIONS_PER_BOAT = 10  # 10-position chain structure

# Force reimport of dependent modules
import importlib
import sailing_scheduler.generator
importlib.reload(sailing_scheduler.generator)
import sailing_scheduler.validator
importlib.reload(sailing_scheduler.validator)
import sailing_scheduler.metrics
importlib.reload(sailing_scheduler.metrics)
import sailing_scheduler.export
importlib.reload(sailing_scheduler.export)

from sailing_scheduler.generator import generate_schedule
from sailing_scheduler.validator import validate_schedule
from sailing_scheduler.export import export_schedule_tsv
from sailing_scheduler.metrics import calculate_metrics

OUTPUT_FILE = Path(__file__).parent / "23_competitors_90_races.tsv"


def main():
    print("Generating schedule: 23 competitors, 90 races (with 3 sit-outs per round)...")
    print("Chain structure: 10 positions per boat, 5 groups")
    print("=" * 60)
    
    schedule = generate_schedule()
    
    print(f"\nCompetitors: {len(schedule.competitors)}")
    print(f"Races: {len(schedule.races)}")
    
    # Race count distribution
    race_counts = {}
    for c in schedule.competitors:
        count = len(schedule.get_races_for_competitor(c))
        race_counts[count] = race_counts.get(count, 0) + 1
    print(f"Race distribution: {dict(sorted(race_counts.items()))}")
    
    # Validate
    report = validate_schedule(schedule)
    print(f"\n{report}")
    
    if not report.all_passed:
        print("\n⚠️  Schedule has validation issues!")
        sys.exit(1)
    
    # Metrics
    metrics = calculate_metrics(schedule)
    print(f"\n{metrics}")
    
    # Export
    export_schedule_tsv(schedule, str(OUTPUT_FILE))
    print(f"\n✓ Schedule exported to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

