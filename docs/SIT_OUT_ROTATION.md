# Sit-Out Rotation for 25 Competitors

This document explains how the scheduler handles 25 competitors when the chain structure requires exactly 24 per round.

## The Problem

The chain-based scheduling algorithm assigns 12 competitors to each boat set per round (24 total). With 25 competitors, one must sit out each round.

**The math:**
- 96 races × 4 competitors = 384 competitor-race slots
- 384 / 25 = 15.36 races per person (doesn't divide evenly)
- 384 / 24 = 16 races per person (the chain structure's natural fit)

## The Solution: "Most Races Sits Out"

Before each round, the competitor who has raced the **most times so far** sits out. This simple rule guarantees excellent interruptibility.

### Why This Works

| After Round | Who Sat Out | Race Counts | Max Spread |
|-------------|-------------|-------------|------------|
| 1 | Anyone (all at 0) | 1 person: 0, others: 2 | **2** |
| 2 | Someone with 2 races | 2 people: 2, others: 4 | **2** |
| 3 | Someone with 4 races | 3 people: 4, others: 6 | **2** |
| ... | ... | ... | **2** |
| 8 | Someone with 16 races | 8 people: 14, others: 16 | **2** |

By always choosing from the "has raced most" group, the spread never exceeds 2 races.

### Final Distribution

After 8 rounds:
- **8 competitors** sit out once → **14 races each**
- **17 competitors** never sit out → **16 races each**
- **Maximum spread: 2 races**

## Interruptibility Guarantee

If the competition is cut short at **any point**:
- Everyone has raced within **2 races** of each other
- The "sit-out debt" is always paid by those who are ahead
- No competitor falls significantly behind

This is crucial since competitions often don't complete all scheduled races.

## Implementation

### Sit-Out Selection

```python
def _select_sit_out(competitors: list[Competitor], race_counts: dict[int, int]) -> Competitor:
    """Select the competitor with the most races to sit out."""
    return max(competitors, key=lambda c: race_counts[c.id])
```

### Round Generation

For each round:
1. Select sit-out competitor (most races)
2. Assign remaining 24 to chain positions (12 per boat)
3. Generate races as normal
4. Update race counts

### Validation

The validator allows:
- 14-16 races per competitor (instead of exactly 16)
- 0 or 2 races per round per competitor (instead of exactly 2)
- Max spread of 2 at any checkpoint

## Comparison to 24 Competitors

| Aspect | 24 Competitors | 25 Competitors |
|--------|----------------|----------------|
| Races per person | Exactly 16 | 14-16 |
| Per-round participation | All race twice | 24 race twice, 1 sits out |
| Max spread at any point | 0 | 2 |
| Interruptibility | Perfect | Excellent |

## Edge Cases

### Tie-Breaking

When multiple competitors have the same race count (common early on), the algorithm picks randomly among them. This naturally distributes sit-outs across competitors.

### Boundary Constraints

The sit-out competitor is excluded **before** boundary constraint checking. This means:
- They won't appear in `prev_adjacent_boundary` or `prev_boat_*_boundary` sets
- When they return next round, they're treated as "fresh" for positioning

