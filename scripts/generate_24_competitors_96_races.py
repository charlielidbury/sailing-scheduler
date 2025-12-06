#!/usr/bin/env python3
"""Generate a schedule for 24 competitors with 96 races."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Must configure BEFORE any other sailing_scheduler imports
import sailing_scheduler.models as models
models.NUM_COMPETITORS = 24
models.NUM_RACES = 96
models.RACES_PER_COMPETITOR = 16
models.MIN_RACES_PER_COMPETITOR = 16  # No sit-outs, everyone races same amount
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

OUTPUT_FILE = Path(__file__).parent / "24_competitors_96_races.tsv"


def main():
    print("Generating schedule: 24 competitors, 96 races...")
    print("=" * 50)
    
    schedule = generate_schedule()
    
    print(f"\nCompetitors: {len(schedule.competitors)}")
    print(f"Races: {len(schedule.races)}")
    
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
