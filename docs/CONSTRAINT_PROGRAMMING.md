# Constraint Programming / SAT Solver Approach

## Goal
Formulate the schedule as a constraint satisfaction problem (CSP) or satisfiability problem (SAT) and use a solver to find optimal solutions.

## Why Constraint Programming?

- **Guaranteed optimal**: Solvers can prove optimality or find the best solution within constraints
- **Declarative**: Specify WHAT you want, not HOW to find it
- **Handles complex constraints**: Solvers are designed for exactly this type of problem
- **Can optimize multiple objectives**: Maximize proper double outings while satisfying all constraints

## Recommended Tools

### Option 1: Google OR-Tools (Recommended)
```bash
pip install ortools
```
- CP-SAT solver is state-of-the-art
- Good Python API
- Can handle optimization objectives

### Option 2: Z3
```bash
pip install z3-solver
```
- SMT solver from Microsoft Research
- Very powerful for constraint problems

### Option 3: python-constraint
```bash
pip install python-constraint
```
- Pure Python, simpler but slower
- Good for prototyping

## Problem Formulation

### Decision Variables

For each race R (1-48) and each boat position P (1-4), define which competitor occupies it:

```python
# competitor[race][position] = competitor_id (0-23)
# position 0 = team_a.competitor1 (boat 7)
# position 1 = team_a.competitor2 (boat 8)
# position 2 = team_b.competitor1 (boat 10)
# position 3 = team_b.competitor2 (boat 11)

competitor = [[model.NewIntVar(0, 23, f'c_{r}_{p}') for p in range(4)] for r in range(48)]
```

### Hard Constraints

#### 1. All Different Within Race
Each race has 4 different competitors:
```python
for r in range(48):
    model.AddAllDifferent(competitor[r])
```

#### 2. Exactly 8 Races Per Competitor
```python
for c in range(24):
    # Count how many races competitor c appears in
    appearances = []
    for r in range(48):
        for p in range(4):
            b = model.NewBoolVar(f'appears_{c}_{r}_{p}')
            model.Add(competitor[r][p] == c).OnlyEnforceIf(b)
            model.Add(competitor[r][p] != c).OnlyEnforceIf(b.Not())
            appearances.append(b)
    model.Add(sum(appearances) == 8)
```

#### 3. No Adjacent Races
Competitor cannot be in Race N and Race N+1:
```python
for c in range(24):
    for r in range(47):
        in_race_r = model.NewBoolVar(f'in_{c}_{r}')
        in_race_r_plus_1 = model.NewBoolVar(f'in_{c}_{r+1}')
        # Define in_race_r and in_race_r_plus_1 based on competitor variables
        model.Add(in_race_r + in_race_r_plus_1 <= 1)
```

#### 4. Unique Teammates
For each competitor, the 8 teammates across 8 races must all be different:
```python
for c in range(24):
    teammates = []  # List of teammate variables for competitor c
    # For each race c is in, find their teammate
    # (same team = positions 0,1 or positions 2,3)
    model.AddAllDifferent(teammates)
```

#### 5. Two Races Per Round
```python
for c in range(24):
    for round_num in range(4):
        start_race = round_num * 12
        end_race = start_race + 12
        # Count races in this round for competitor c
        model.Add(races_in_round == 2)
```

#### 6. No Triple Outings
If competitor is in races N and N+2 (same boat set), they cannot be in N+4:
```python
# For each potential triple: (N, N+2, N+4) on same boat set
for c in range(24):
    for base in range(1, 45, 2):  # Odd races for boat set A
        in_n = is_in_race(c, base)
        in_n2 = is_in_race(c, base + 2)
        in_n4 = is_in_race(c, base + 4)
        model.Add(in_n + in_n2 + in_n4 <= 2)
```

#### 7. Minimum Opponent Diversity
Each competitor faces at least 12 unique opponents:
```python
for c in range(24):
    unique_opponents = count_unique_opponents(c)
    model.Add(unique_opponents >= 12)
```

### Optimization Objective

Maximize proper double outings:
```python
proper_double_outings = []

for c in range(24):
    for r in range(1, 47, 2):  # Potential double outing pairs
        # Check if c is in both race r and race r+2 in SAME position
        same_position = model.NewBoolVar(f'same_pos_{c}_{r}')
        # ... define same_position based on competitor variables
        proper_double_outings.append(same_position)

model.Maximize(sum(proper_double_outings))
```

## Implementation Skeleton (OR-Tools)

```python
from ortools.sat.python import cp_model

def generate_schedule_csp():
    model = cp_model.CpModel()
    
    # Decision variables
    competitor = [[model.NewIntVar(0, 23, f'c_{r}_{p}') 
                   for p in range(4)] for r in range(48)]
    
    # Add constraints (see above)
    add_all_different_constraints(model, competitor)
    add_race_count_constraints(model, competitor)
    add_adjacent_race_constraints(model, competitor)
    add_unique_teammate_constraints(model, competitor)
    add_round_structure_constraints(model, competitor)
    add_no_triple_outing_constraints(model, competitor)
    add_opponent_diversity_constraints(model, competitor)
    
    # Optimization objective
    add_double_outing_objective(model, competitor)
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300  # 5 minute timeout
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return extract_schedule(solver, competitor)
    else:
        raise RuntimeError("No solution found")
```

## Expected Benefits

1. **Provably optimal**: If solver finds solution, it's the best possible
2. **Handles all constraints simultaneously**: No need for multi-phase approach
3. **Can explore trade-offs**: Add weights to different objectives

## Challenges

1. **Encoding complexity**: Translating constraints to solver format is tricky
2. **Runtime**: Large problems can take minutes to hours
3. **Learning curve**: Need to understand solver API and idioms

## Success Criteria

1. All validation tests pass
2. Proper double outings > 40 (current best)
3. Runtime < 5 minutes
4. Solver reports optimal or near-optimal

## Files to Modify/Create

- Create `src/sailing_scheduler/csp_generator.py` with new solver-based approach
- Modify `src/sailing_scheduler/generator.py` to use CSP solution
- Add `ortools` to dependencies in `pyproject.toml`

