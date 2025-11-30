# Simulated Annealing Approach

## Goal
Replace the current greedy local optimization with simulated annealing to escape local optima and find better schedules with more proper double outings.

## Why Simulated Annealing?

The current algorithm uses greedy optimization - it only accepts changes that immediately improve the score. This gets stuck in local optima.

Simulated annealing can temporarily accept worse solutions, allowing it to escape local optima and potentially find globally better solutions.

## Algorithm Overview

```python
def simulated_annealing(initial_schedule):
    schedule = initial_schedule
    best_schedule = schedule
    best_score = score(schedule)
    
    temperature = 1.0
    cooling_rate = 0.9999
    min_temperature = 0.001
    
    while temperature > min_temperature:
        # Generate neighbor by random modification
        new_schedule = random_neighbor(schedule)
        
        # Only consider if hard constraints satisfied
        if not satisfies_hard_constraints(new_schedule):
            continue
        
        new_score = score(new_schedule)
        delta = new_score - score(schedule)
        
        # Accept if better, or probabilistically if worse
        if delta > 0 or random() < exp(delta / temperature):
            schedule = new_schedule
            
            if new_score > best_score:
                best_score = new_score
                best_schedule = schedule
        
        temperature *= cooling_rate
    
    return best_schedule
```

## Scoring Function

The score should prioritize hard constraints, then optimize soft constraints:

```python
def score(schedule):
    # Hard constraints - must be 0 for valid schedule
    if has_adjacent_violations(schedule): return -10000
    if has_duplicate_teammates(schedule): return -10000
    if has_triple_outings(schedule): return -10000
    if min_opponents(schedule) < 12: return -5000
    
    # Soft constraints - maximize
    score = 0
    score += proper_double_outings(schedule) * 100  # Primary objective
    score -= single_outings(schedule) * 10
    score += min_visibility(schedule) * 5
    
    return score
```

## Neighbor Generation

Define several "move" operations that create neighboring schedules:

### Move 1: Swap Within Team
Swap `competitor1` and `competitor2` within a team in one race.
- Changes boat positions (7↔8 or 10↔11)
- Does NOT change who is teammates
- Can improve proper double outings

### Move 2: Swap Across Teams
Swap one competitor from Team A with one from Team B in a race.
- Changes teammate pairings
- May create/resolve duplicate teammate conflicts
- Changes opponent relationships

### Move 3: Swap Between Races
Swap a competitor's position between two different races.
- Must maintain exactly 8 races per competitor
- Must not create adjacent race violations

### Move 4: Rotate Boat Assignment
Rotate all 4 competitors in a race to different positions.
- Preserves team structure but changes all boat positions

## Implementation Suggestions

1. **Start from current algorithm's output**: Use the chain-based generation as the initial schedule, then apply simulated annealing to improve it.

2. **Focus on proper double outings**: The main improvement opportunity is increasing from 50% to higher.

3. **Maintain hard constraints**: Only accept moves that keep the schedule valid. Reject moves that violate:
   - Adjacent race constraint
   - Exactly 8 races per competitor
   - 2 races per round per competitor
   - Unique teammates
   - Max 2 consecutive per boat set

4. **Tune parameters**: 
   - Initial temperature affects exploration range
   - Cooling rate affects convergence speed
   - Number of iterations affects solution quality

5. **Multiple restarts**: Run simulated annealing multiple times from different starting points.

## Expected Improvements

| Metric | Current | Target |
|--------|---------|--------|
| Proper double outings | 40 (50%) | 50-60+ (62-75%) |
| Single outings | 32 | 20-25 |

## Success Criteria

The implementation is successful if:
1. All existing validation tests pass
2. Proper double outings ≥ 45 (improvement over current 40)
3. Runtime reasonable (< 60 seconds)

## Files to Modify

- `src/sailing_scheduler/generator.py` - Replace or augment `_optimize_double_outings()`
- May add new module `src/sailing_scheduler/annealing.py`

