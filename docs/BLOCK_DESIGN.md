# Block Design / Combinatorial Approach

## Goal
Use mathematical structures from combinatorics (block designs, Latin squares, etc.) to construct schedules with provably good properties.

## Why Block Designs?

The sailing scheduling problem has structure similar to classic combinatorics problems:
- **Balanced Incomplete Block Designs (BIBD)**: Ensure each pair of elements appears together a fixed number of times
- **Resolvable designs**: Can be partitioned into parallel classes (like our rounds)
- **Latin squares**: Each element appears exactly once in each row and column

Mathematical constructions can guarantee optimal properties rather than searching for them.

## Relevant Mathematical Structures

### 1. Balanced Incomplete Block Design (BIBD)
A (v, b, r, k, λ)-BIBD is a set of v elements arranged into b blocks, where:
- Each block contains k elements
- Each element appears in r blocks
- Each pair of elements appears in λ blocks together

**Our problem mapping:**
- v = 24 competitors
- k = 4 competitors per race
- r = 8 races per competitor
- We want λ = 1 for teammates (unique teammates)
- Opponents can have λ ≥ 1

### 2. Resolvable Design
A design is resolvable if blocks can be partitioned into "parallel classes" where each element appears exactly once per class.

**Our mapping:**
- 4 rounds = 4 parallel classes
- Each round has 12 races
- Each competitor appears in exactly 2 races per round (not 1, so not directly resolvable)

### 3. Kirkman Schoolgirl Problem
Classic problem: 15 girls walk in groups of 3 for 7 days such that no pair walks together twice.

**Our variant:** 24 competitors in groups of 4 (races) for multiple rounds, with teammate and opponent constraints.

## Construction Approaches

### Approach 1: Difference Sets
Use modular arithmetic to generate balanced pairings.

```python
def generate_from_differences(n=24):
    """Generate races using difference sets in Z_n"""
    # For each race, positions are determined by adding a base to a difference pattern
    base_pattern = [0, 1, 6, 7]  # Example pattern with good difference properties
    
    races = []
    for shift in range(n):
        race = [(pos + shift) % n for pos in base_pattern]
        races.append(race)
    
    return races
```

The challenge is finding base patterns that satisfy all constraints.

### Approach 2: Steiner Systems
A Steiner system S(t, k, n) is a set of k-element blocks from n elements where every t-element subset appears in exactly one block.

**S(2, 4, 24)** would give us blocks of 4 where every pair appears together exactly once - perfect for unique teammates! Unfortunately S(2,4,24) doesn't exist, but we can use approximations.

### Approach 3: Room Squares and Whist Tournaments
Room squares and whist tournament designs are specifically for scheduling games where:
- Players are paired into teams
- Each player partners with each other player exactly once
- Each player opposes each other player the same number of times

This is very close to our problem!

```python
def construct_whist_tournament(n=24):
    """
    Construct a whist tournament for n players.
    
    A whist tournament has n-1 rounds where each round consists of n/4 games.
    Each game has 2 teams of 2 players.
    """
    # Use known construction methods for whist tournaments
    # Reference: "Whist Tournaments" by Anderson and Finizio
    pass
```

### Approach 4: Round-Robin with Team Rotation
Adapt round-robin tournament scheduling:

```python
def round_robin_teams(competitors):
    """
    Generate matches using round-robin with rotating teams.
    
    Fix one competitor, rotate others around a circle.
    """
    n = len(competitors)
    fixed = competitors[0]
    rotating = competitors[1:]
    
    rounds = []
    for round_num in range(n - 1):
        round_races = []
        # Fixed plays with first of rotating
        # Then pair up rest of rotating list
        # Rotate list for next round
        rotating = [rotating[-1]] + rotating[:-1]
        rounds.append(round_races)
    
    return rounds
```

## Hybrid Approach: Mathematical Base + Local Optimization

1. **Use mathematical structure for base schedule**: Ensure good theoretical properties
2. **Apply local optimization for boat positions**: Maximize proper double outings

```python
def hybrid_approach():
    # Phase 1: Generate mathematically structured schedule
    base_schedule = generate_from_combinatorial_design()
    
    # This gives us:
    # - Good opponent diversity (by construction)
    # - Unique teammates (by construction)
    # - Balanced race distribution
    
    # Phase 2: Optimize boat positions
    optimized = optimize_boat_positions(base_schedule)
    
    # This improves:
    # - Proper double outings
    # - Single outing count
    
    return optimized
```

## Specific Construction for Our Problem

### Parameters
- 24 competitors
- 48 races (4 rounds × 12 races)
- 4 competitors per race
- 8 races per competitor
- 2 races per competitor per round
- Unique teammates constraint

### Proposed Construction

**Step 1: Partition into 6 groups of 4**
```
Groups: {0,1,2,3}, {4,5,6,7}, {8,9,10,11}, {12,13,14,15}, {16,17,18,19}, {20,21,22,23}
```

**Step 2: Generate races from group combinations**
Each race draws from 2 groups (8 people) and selects 4.
Use a balanced selection ensuring each person from the 8 appears in half the derived races.

**Step 3: Assign to boat positions**
Within each race of 4, assign to positions 7,8,10,11 to create teams.
Ensure teammate uniqueness by careful assignment.

**Step 4: Organize into rounds**
Arrange races so each competitor appears exactly twice per round.

## Implementation Considerations

### Advantages
- Guarantees on properties (opponent diversity, teammate uniqueness)
- May find solutions unreachable by random search
- Elegant and verifiable

### Challenges
- May not directly optimize for proper double outings
- Mathematical constructions can be complex
- May need adaptation for specific constraints (max 2 consecutive, rounds, etc.)

## Resources

- **"Combinatorial Designs" by Stinson**: Comprehensive textbook on block designs
- **"Handbook of Combinatorial Designs" by Colbourn and Dinitz**: Reference for specific constructions
- **Whist tournament constructions**: Papers by Anderson, Finizio, Leonard

## Success Criteria

1. All validation tests pass
2. Can prove/explain why certain properties are guaranteed
3. Proper double outings ≥ 40 (at least match current)
4. Potentially discover theoretical limits on what's achievable

## Files to Modify/Create

- Create `src/sailing_scheduler/combinatorial.py` with mathematical constructions
- May need `src/sailing_scheduler/design_tables.py` for pre-computed structures
- Modify generator to use combinatorial base with local optimization

