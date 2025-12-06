#!/usr/bin/env python3
"""Generate a schedule for 25 competitors with 96 races (1 sit-out per round)."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Must configure BEFORE any other sailing_scheduler imports
import sailing_scheduler.models as models
models.NUM_COMPETITORS = 25
models.NUM_RACES = 96
models.RACES_PER_COMPETITOR = 16  # Max (never sit out)
models.MIN_RACES_PER_COMPETITOR = 14  # Min (sit out once)
models.COMPETITORS_PER_ROUND = 24

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

OUTPUT_FILE = Path(__file__).parent / "25_competitors_96_races.tsv"


def main():
    print("Generating schedule: 25 competitors, 96 races (with sit-out rotation)...")
    print("=" * 50)
    
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
