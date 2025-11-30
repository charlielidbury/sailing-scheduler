# Current Algorithm

This document describes the algorithm currently implemented in `src/sailing_scheduler/generator.py`.

## Overview

The current approach uses a **chain-based structure** with **random search** and **local optimization**.

## Phase 1: Chain Structure Generation

### The Chain Pattern
Within each round, each boat set uses a "chain" of 6 race groups where consecutive groups share 2 positions:

```
Group 0: positions [0, 1, 2, 3]   → Race 1 (or 2 for boat B)
Group 1: positions [2, 3, 4, 5]   → Race 3 (or 4)
Group 2: positions [4, 5, 6, 7]   → Race 5 (or 6)
Group 3: positions [6, 7, 8, 9]   → Race 7 (or 8)
Group 4: positions [8, 9, 10, 11] → Race 9 (or 10)
Group 5: positions [10, 11, 0, 1] → Race 11 (or 12)
```

This creates natural "double outings" because positions 2-3 appear in both Groups 0 and 1, positions 4-5 in Groups 1 and 2, etc.

### Competitor Assignment
For each round:
1. Randomly shuffle all 24 competitors
2. Assign first 12 to Boat Set A positions [0-11]
3. Assign remaining 12 to Boat Set B positions [0-11]
4. Apply boundary constraints (see below)

### Boundary Constraints
To prevent violations at round boundaries:

**Adjacent Race Constraint**: The last race of Boat Set B in round N (Race 12, 24, 36) overlaps with the first race of Boat Set A in round N+1 (Race 13, 25, 37). Competitors in Boat B positions [0, 1, 10, 11] of round N cannot be in Boat A positions [0, 1, 2, 3] of round N+1.

**Consecutive Race Constraint**: Competitors in positions [0, 1, 10, 11] of a boat in round N race in the last chain group. They cannot be in positions [0, 1, 2, 3] of the same boat in round N+1 (which would create a triple outing across the boundary).

### Team Formation
For each race's 4 competitors, form 2 teams of 2:
- Try all 3 possible pairings: (0,1 vs 2,3), (0,2 vs 1,3), (0,3 vs 1,2)
- Choose the pairing that minimizes duplicate teammates
- If all pairings would create duplicates, choose the one with fewest

## Phase 2: Local Optimization for Double Outings

After generating the base schedule, optimize boat positions within teams to maximize **proper double outings** (same boat position across races N and N+2).

### The Problem
Two competitors continue from race N to race N+2. If they're on different teams in N but same team in N+2 (or vice versa), they end up in different boat positions and must switch boats.

### The Solution
For each consecutive race pair:
1. Identify the 2 shared competitors
2. Check their boat positions in both races
3. Try swapping within teams:
   - Swap `team_a.competitor1` ↔ `team_a.competitor2` (swaps positions 7 and 8)
   - Swap `team_b.competitor1` ↔ `team_b.competitor2` (swaps positions 10 and 11)
4. Apply swap if it increases the number of aligned positions
5. Multiple passes until no improvement

### Important: Swapping Within Teams Doesn't Change Teammates
Swapping competitor1 and competitor2 within a team only changes their **boat positions**, not who they're teamed with. The same 2 people are still teammates.

## Phase 3: Seed Search

The algorithm tries multiple random seeds (up to 200) and keeps the best schedule based on:
1. First filter: must have ≥12 minimum unique opponents
2. Then select: highest number of proper double outings

## Current Performance

- **Proper double outings**: 40/80 (50%)
- **Single outings**: 32
- **Duplicate teammates**: 0
- **Adjacent violations**: 0
- **Min opponents**: 12
- **Visibility**: 14-18

## Limitations

1. **Greedy optimization**: The local swap optimization can get stuck in local optima
2. **Chain structure rigidity**: The chain pattern inherently limits some configurations
3. **Limited search space**: Only 200 seeds explored
4. **No global optimization**: Each race pair optimized independently

## Code Structure

```
generator.py
├── generate_schedule()           # Main entry point, seed search
├── _try_generate_chain_schedule() # Generate one schedule attempt
├── _find_round_assignment()      # Assign competitors to boat positions
├── _generate_chain_races_careful() # Create races from chain groups
├── _form_teams_optimally()       # Choose best team pairing
└── _optimize_double_outings()    # Post-process to improve boat alignment
```

