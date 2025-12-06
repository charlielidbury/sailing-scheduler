#!/usr/bin/env python3
"""
Substitute competitor numbers with pair names in a schedule.

Usage:
    python scripts/substitute_pairs.py [schedule_file]

If no schedule file is provided, it auto-selects based on the number of pairs in pairs.tsv.

The script reads pairs.tsv and maps:
- Row 2 (first pair) → Competitor 0
- Row 3 (second pair) → Competitor 1
- etc.

To exclude pairs: move them to the end of pairs.tsv, then run with a smaller schedule.
"""

import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PAIRS_FILE = PROJECT_ROOT / "pairs.tsv"
OUTPUT_FILE = PROJECT_ROOT / "schedule.tsv"

# Available schedules by competitor count
SCHEDULES = {
    23: SCRIPT_DIR / "23_10_pos_chain.tsv",
    24: SCRIPT_DIR / "24_competitors_96_races.tsv",
    25: SCRIPT_DIR / "25_competitors_96_races.tsv",
}


def load_pairs(filepath: Path, limit: int | None = None) -> dict[int, str]:
    """Load pairs from TSV, returning {competitor_id: 'FirstName1/FirstName2'}."""
    pairs = {}
    with open(filepath, "r") as f:
        lines = f.readlines()
    
    # Skip header (line 0)
    for i, line in enumerate(lines[1:]):
        if limit is not None and i >= limit:
            break
        parts = line.strip().split("\t")
        if len(parts) >= 2:
            # Extract first names only
            first1 = parts[0].split()[0] if parts[0].strip() else parts[0]
            first2 = parts[1].split()[0] if parts[1].strip() else parts[1]
            pair_name = f"{first1}/{first2}"
            pairs[i] = pair_name
    
    return pairs


def substitute_schedule(schedule_path: Path, pairs: dict[int, str], output_path: Path):
    """Read schedule, substitute numbers with pair names, write to output."""
    with open(schedule_path, "r") as f:
        lines = f.readlines()
    
    output_lines = []
    for line in lines:
        parts = line.rstrip("\n").split("\t")
        new_parts = []
        for col_idx, part in enumerate(parts):
            stripped = part.strip()
            # Competitor columns: 1-4 (boat set A) and 5-8 (boat set B)
            # Column 0 = Race number, Columns 9-10 = Min/Max
            if col_idx in (1, 2, 3, 4, 5, 6, 7, 8) and stripped.isdigit():
                comp_id = int(stripped)
                if comp_id in pairs:
                    new_parts.append(pairs[comp_id])
                else:
                    new_parts.append(part)  # Keep original if no mapping
            else:
                new_parts.append(part)
        output_lines.append("\t".join(new_parts))
    
    with open(output_path, "w") as f:
        f.write("\n".join(output_lines))
    
    print(f"✓ Written to {output_path}")


def main():
    # Load all pairs to count them
    all_pairs = load_pairs(PAIRS_FILE)
    num_pairs = len(all_pairs)
    print(f"Found {num_pairs} pairs in {PAIRS_FILE}")
    
    # Determine which schedule to use
    if len(sys.argv) > 1:
        schedule_path = Path(sys.argv[1])
        if not schedule_path.is_absolute():
            schedule_path = PROJECT_ROOT / schedule_path
    else:
        # Auto-select based on pair count
        if num_pairs >= 25:
            schedule_path = SCHEDULES[25]
            num_competitors = 25
        elif num_pairs >= 24:
            schedule_path = SCHEDULES[24]
            num_competitors = 24
        elif num_pairs >= 23:
            schedule_path = SCHEDULES[23]
            num_competitors = 23
        else:
            print(f"Error: Need at least 23 pairs, found {num_pairs}")
            sys.exit(1)
        
        print(f"Auto-selected {num_competitors}-competitor schedule")
    
    if not schedule_path.exists():
        print(f"Error: Schedule file not found: {schedule_path}")
        sys.exit(1)
    
    # Detect how many competitors the schedule needs (from columns 1-4 only)
    with open(schedule_path, "r") as f:
        lines = f.readlines()
    
    competitor_ids = set()
    for line in lines[2:]:  # Skip header rows
        parts = line.strip().split("\t")
        for col_idx in (1, 2, 3, 4, 5, 6, 7, 8):  # Competitor columns for both boat sets
            if col_idx < len(parts) and parts[col_idx].strip().isdigit():
                competitor_ids.add(int(parts[col_idx].strip()))
    
    max_competitor = max(competitor_ids) if competitor_ids else 0
    num_needed = max_competitor + 1  # 0-indexed
    
    print(f"Schedule needs {num_needed} competitors (0-{max_competitor})")
    
    if num_pairs < num_needed:
        print(f"Error: Not enough pairs! Have {num_pairs}, need {num_needed}")
        print(f"Either add more pairs to pairs.tsv or use a smaller schedule.")
        sys.exit(1)
    
    # Load only the pairs we need
    pairs = load_pairs(PAIRS_FILE, limit=num_needed)
    print(f"Using first {num_needed} pairs from pairs.tsv")
    
    # Substitute and output
    substitute_schedule(schedule_path, pairs, OUTPUT_FILE)
    
    # Show mapping
    print(f"\nPair mapping:")
    for comp_id, pair_name in sorted(pairs.items()):
        print(f"  {comp_id:2d} → {pair_name}")


if __name__ == "__main__":
    main()

