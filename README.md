# Sailing Competition Schedule Generator

This repo generates schedules for sailing competitions. The goal is to create fair, practical schedules that maximize competitor experience while satisfying all constraints.

## Competition Structure

### Basic Setup
- **24 competitors** (each "competitor" is actually a pair of people - helm & crew - but they always race together so we treat them as one unit)
- **48 races** total
- **2 boat sets** that alternate: Boat Set A (odd races: 1, 3, 5...) and Boat Set B (even races: 2, 4, 6...)
- **4 boats per race**: 2 boats on Team A vs 2 boats on Team B
- **1 competitor per boat** (so 4 competitors per race)

### Boat Positions
Each boat set has 4 specific boat positions:
- **Boat Set A**: Pink-7, Pink-8 (Team A) vs Black Stripe-10, Black Stripe-11 (Team B)
- **Boat Set B**: Green Circle-7, Green Circle-8 (Team A) vs Black Diamond-10, Black Diamond-11 (Team B)

In the data model:
- `team_a.competitor1` → position 7 (first column)
- `team_a.competitor2` → position 8 (second column)
- `team_b.competitor1` → position 10 (third column)
- `team_b.competitor2` → position 11 (fourth column)

**The order matters!** Competitor1 and competitor2 are in different physical boats.

### Concurrent Races
Races on different boat sets run concurrently with staggered starts:

| Boat Set A | Boat Set B |
|------------|------------|
| Race 1     |            |
| Race 1     | Race 2     |
| Race 3     | Race 2     |
| Race 3     | Race 4     |
|            | Race 4     |

This means **Race N and Race N+1 overlap in time** - a competitor cannot be in both.

### Rounds
The schedule is divided into 4 rounds of 12 races each:
- Round 1: Races 1-12
- Round 2: Races 13-24
- Round 3: Races 25-36
- Round 4: Races 37-48

Each competitor races exactly **twice per round** (once per boat set ideally as a double outing).

---

## Hard Constraints (MUST be satisfied)

1. **No adjacent races**: A competitor cannot race in both Race N and Race N+1 (they overlap in time)

2. **Exactly 8 races per competitor**: Each of the 24 competitors races exactly 8 times

3. **Unique teammates**: A competitor must never have the same teammate twice across all 8 races (8 races = 8 unique teammates)

4. **Max 2 consecutive races per boat set**: No "triple outings" - if a competitor races in N and N+2, they cannot also race in N+4 on the same boat set

5. **Round structure**: Each competitor races exactly twice per round (enables fair interruption)

6. **Minimum opponent diversity**: Each competitor must face at least 12 unique opponents across their 8 races

---

## Soft Constraints (Optimize for)

### Double Outings
A **double outing** is when a competitor races in Race N and Race N+2 (same boat set, with one race gap).

A **proper double outing** is when they stay in the **same boat position** (same column) for both races. This is strongly preferred because:
- No need to switch boats between races
- Less physical scrambling
- More relaxed experience

**Goal**: Maximize proper double outings. Current best: 40 out of 80 potential (50%).

### Single Outings
When a competitor has races that don't form double outings (e.g., races 5 and 13), each becomes a "single outing" requiring separate trips to the water.

**Goal**: Minimize single outings. Current: 32 single outings across all competitors.

### Visibility
How many unique other competitors does each person "see" (race with or against)?

**Goal**: Maximize minimum visibility. Current: min 14, max 18.

---

## Quality Metrics

| Metric | Current Best | Ideal |
|--------|--------------|-------|
| Duplicate teammates | 0 | 0 |
| Adjacent race violations | 0 | 0 |
| Proper double outings | 40/80 (50%) | 80/80 (100%) |
| Single outings | 32 | 0 |
| Min unique opponents | 12 | 23 |
| Min visibility | 14 | 23 |

---

## Running the Code

```bash
# Install
pip install -e .

# Generate schedule
python -c "from sailing_scheduler import generate_schedule, export_schedule_tsv; s = generate_schedule(); export_schedule_tsv(s, 'schedule.tsv')"

# Run tests
pytest tests/

# View metrics
python -c "from sailing_scheduler import generate_schedule; from sailing_scheduler.metrics import calculate_metrics; print(calculate_metrics(generate_schedule()))"
```

---

## Output Format

The schedule exports to TSV with columns:
```
Race | Pink(7,8) | Black Stripe(10,11) | Green Circle(7,8) | Black Diamond(10,11)
```

Each row shows which competitors are in which boat positions for that race. Odd races fill Boat Set A columns, even races fill Boat Set B columns.

---

## Validation

The `validator.py` module checks all hard constraints. All checks must pass:
- `correct_number_of_competitors`: Exactly 24
- `correct_number_of_races`: Exactly 48
- `boat_sets_alternate`: Odd races = A, even = B
- `race_numbers_sequential`: 1 through 48
- `each_race_has_four_competitors`: 4 unique per race
- `req1_no_adjacent_races`: No N and N+1 for same person
- `req2_exactly_eight_races`: 8 per competitor
- `req3_unique_teammates`: No duplicate teammates
- `req4_5_two_race_outings`: Reasonable number of double outings
- `req6_schedule_balance`: Even distribution across rounds
- `req6_round_structure`: 2 races per competitor per round
- `req7_max_consecutive_races`: No triple outings
- `opponent_diversity`: At least 12 unique opponents each

---

## Algorithm Documentation

See the `docs/` folder for detailed algorithm documentation:
- `CURRENT_ALGORITHM.md` - How the current implementation works
- Alternative approaches for potential improvement
