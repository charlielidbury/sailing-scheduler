# Genetic Algorithm Approach

## Goal
Use evolutionary computation to breed better schedules over generations, combining good features from different schedules.

## Why Genetic Algorithms?

- **Population-based**: Maintains diversity of solutions, reducing chance of getting stuck
- **Crossover**: Can combine good parts from different schedules
- **Parallel exploration**: Multiple candidate solutions evolve simultaneously
- **No gradient needed**: Works well for combinatorial optimization

## Algorithm Overview

```python
def genetic_algorithm(population_size=100, generations=500):
    # Initialize population
    population = [generate_random_valid_schedule() for _ in range(population_size)]
    
    for generation in range(generations):
        # Evaluate fitness
        fitness_scores = [fitness(schedule) for schedule in population]
        
        # Selection (tournament or roulette wheel)
        selected = selection(population, fitness_scores)
        
        # Crossover
        offspring = []
        for i in range(0, len(selected), 2):
            child1, child2 = crossover(selected[i], selected[i+1])
            offspring.extend([child1, child2])
        
        # Mutation
        for schedule in offspring:
            if random() < mutation_rate:
                mutate(schedule)
        
        # Repair invalid schedules
        offspring = [repair(s) if not is_valid(s) else s for s in offspring]
        
        # Replace population (elitism: keep best from previous generation)
        population = elitism_replacement(population, offspring, fitness_scores)
    
    return best_schedule(population)
```

## Chromosome Representation

### Option 1: Direct Encoding
Represent schedule as a 48×4 matrix of competitor IDs:
```python
chromosome = [
    [3, 17, 8, 21],   # Race 1: positions 7,8,10,11
    [5, 12, 1, 19],   # Race 2
    ...
]
```

### Option 2: Permutation Encoding (Recommended)
For each round, represent as a permutation of competitors to positions:
```python
# Round 1, Boat A: which competitors at positions 0-11
# Round 1, Boat B: which competitors at positions 0-11
chromosome = {
    'round_1_boat_a': [3, 17, 8, 21, 5, 12, 1, 19, 7, 23, 0, 14],
    'round_1_boat_b': [2, 6, 9, 11, 4, 15, 10, 22, 13, 18, 16, 20],
    'round_2_boat_a': [...],
    ...
}
```

This naturally ensures each competitor appears exactly once per boat per round.

## Fitness Function

```python
def fitness(schedule):
    # Penalize hard constraint violations heavily
    penalty = 0
    penalty += count_adjacent_violations(schedule) * 10000
    penalty += count_duplicate_teammates(schedule) * 10000
    penalty += count_triple_outings(schedule) * 10000
    
    if min_unique_opponents(schedule) < 12:
        penalty += (12 - min_unique_opponents(schedule)) * 1000
    
    # Reward good properties
    reward = 0
    reward += proper_double_outings(schedule) * 100
    reward += min_visibility(schedule) * 10
    reward -= single_outings(schedule) * 5
    
    return reward - penalty
```

## Crossover Operators

### Round-Based Crossover
Exchange entire rounds between parents:
```python
def crossover_rounds(parent1, parent2):
    child1, child2 = copy(parent1), copy(parent2)
    # Swap rounds 2 and 3
    for round_num in [2, 3]:
        child1[round_num] = parent2[round_num]
        child2[round_num] = parent1[round_num]
    return child1, child2
```

### Boat-Based Crossover
Exchange boat assignments for specific rounds:
```python
def crossover_boats(parent1, parent2):
    # Child 1: Boat A from parent1, Boat B from parent2 for rounds 1-2
    # Child 2: opposite
    ...
```

### Order Crossover (OX)
For permutation encoding, use standard OX crossover to preserve relative ordering.

## Mutation Operators

### Swap Mutation
Swap two competitors' positions within a race:
```python
def mutate_swap(schedule):
    race = random_race()
    pos1, pos2 = random.sample([0,1,2,3], 2)
    schedule[race][pos1], schedule[race][pos2] = schedule[race][pos2], schedule[race][pos1]
```

### Position Mutation
Move a competitor to a different boat position within their team:
```python
def mutate_position(schedule):
    race = random_race()
    # Swap within team_a (positions 0,1) or team_b (positions 2,3)
    if random() < 0.5:
        schedule[race][0], schedule[race][1] = schedule[race][1], schedule[race][0]
    else:
        schedule[race][2], schedule[race][3] = schedule[race][3], schedule[race][2]
```

### Round Shuffle Mutation
Re-shuffle competitor positions within a round while maintaining constraints.

## Repair Function

After crossover/mutation, schedules may be invalid. Repair by:
1. Fix race counts: Add/remove competitor appearances to get exactly 8 each
2. Fix adjacent violations: Swap competitors between races
3. Fix teammate duplicates: Swap team assignments

```python
def repair(schedule):
    while has_race_count_violations(schedule):
        fix_race_counts(schedule)
    while has_adjacent_violations(schedule):
        fix_adjacent(schedule)
    while has_duplicate_teammates(schedule):
        fix_teammates(schedule)
    return schedule
```

## Selection Methods

### Tournament Selection
```python
def tournament_selection(population, fitness_scores, tournament_size=5):
    selected = []
    for _ in range(len(population)):
        contestants = random.sample(range(len(population)), tournament_size)
        winner = max(contestants, key=lambda i: fitness_scores[i])
        selected.append(population[winner])
    return selected
```

### Elitism
Always keep the best N individuals in the next generation:
```python
def elitism_replacement(old_pop, offspring, old_fitness, elite_count=5):
    # Keep top elite_count from old population
    elite_indices = sorted(range(len(old_pop)), key=lambda i: old_fitness[i], reverse=True)[:elite_count]
    elite = [old_pop[i] for i in elite_indices]
    
    # Fill rest with best offspring
    return elite + sorted(offspring, key=fitness, reverse=True)[:len(old_pop)-elite_count]
```

## Parameters to Tune

| Parameter | Suggested Range | Notes |
|-----------|-----------------|-------|
| Population size | 50-200 | Larger = more diversity, slower |
| Generations | 200-1000 | More = better solutions, slower |
| Mutation rate | 0.01-0.1 | Too high = random search |
| Crossover rate | 0.7-0.9 | How often to crossover |
| Elite count | 2-10 | Preserve best solutions |
| Tournament size | 3-7 | Selection pressure |

## Expected Improvements

| Metric | Current | Target |
|--------|---------|--------|
| Proper double outings | 40 | 50+ |
| Diversity of solutions | 1 | Many good alternatives |

## Success Criteria

1. All validation tests pass
2. Proper double outings ≥ 45
3. Runtime < 2 minutes
4. Population converges to high-quality solutions

## Files to Modify/Create

- Create `src/sailing_scheduler/genetic.py` with GA implementation
- Modify `src/sailing_scheduler/generator.py` to use GA
- Consider adding progress reporting/visualization

