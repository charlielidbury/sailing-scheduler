"""Schedule generation logic."""

from .models import (
    NUM_COMPETITORS,
    NUM_RACES,
    RACES_PER_COMPETITOR,
    BoatSet,
    Competitor,
    Race,
    Schedule,
    Team,
)


def generate_schedule() -> Schedule:
    """
    Generate a valid sailing competition schedule.
    
    The schedule must satisfy the following requirements:
    1. No competitor can race in adjacent races (N and N+1 overlap)
    2. Each competitor participates in exactly 8 races
    3. Each competitor has unique teammates in all 8 races
    4. Prefer two-race-per-outing pattern (race N then race N+2)
    5. Minimize single-race-outings
    6. Schedule should be interruptible via rounds (each competitor races twice per round)
    
    Returns:
        A Schedule object containing all races and competitors.
    """
    # Create all competitors
    competitors = [
        Competitor(id=i, name=f"Competitor_{i}")
        for i in range(NUM_COMPETITORS)
    ]
    
    # Generate the schedule using a round-based approach
    # 4 rounds × 12 races = 48 races total
    # Each competitor races exactly twice per round (via double-outings)
    
    races = _generate_round_based_schedule(competitors)
    
    return Schedule(races=races, competitors=competitors)


def _generate_round_based_schedule(competitors: list[Competitor]) -> list[Race]:
    """
    Generate races using a round-based structure.
    
    Structure per round (12 races):
    - Boat set A: races at positions 1,3,5,7,9,11 (odd indices)
    - Boat set B: races at positions 2,4,6,8,10,12 (even indices)
    
    Double-outing time slots per round:
    - Boat A: (race 1, race 3), (race 5, race 7), (race 9, race 11)
    - Boat B: (race 2, race 4), (race 6, race 8), (race 10, race 12)
    
    Each time slot has 4 competitors who race twice together.
    This gives 3 slots × 4 competitors × 2 boat sets = 24 competitors per round.
    Each competitor gets 2 races per round, for a total of 8 races over 4 rounds.
    """
    races: list[Race] = []
    
    # Pre-compute group assignments for all 4 rounds
    # Each round partitions 24 competitors into 6 groups of 4
    # 3 groups for boat A, 3 groups for boat B
    round_groups = _compute_round_groups()
    
    # Track used teammates to ensure uniqueness
    used_teammates: dict[int, set[int]] = {c.id: set() for c in competitors}
    
    for round_num in range(4):
        round_start_race = round_num * 12 + 1  # Race numbers: 1-12, 13-24, 25-36, 37-48
        groups = round_groups[round_num]
        
        # Groups 0-2 are for boat A (time slots 0, 1, 2)
        # Groups 3-5 are for boat B (time slots 0, 1, 2)
        
        for group_idx, group in enumerate(groups):
            is_boat_a = group_idx < 3
            time_slot = group_idx % 3
            
            boat_set = BoatSet.A if is_boat_a else BoatSet.B
            
            # Calculate race numbers for this time slot
            # Boat A time slots: (1,3), (5,7), (9,11) -> offsets (0,2), (4,6), (8,10)
            # Boat B time slots: (2,4), (6,8), (10,12) -> offsets (1,3), (5,7), (9,11)
            if is_boat_a:
                race_offset_1 = time_slot * 4  # 0, 4, 8
                race_offset_2 = race_offset_1 + 2  # 2, 6, 10
            else:
                race_offset_1 = time_slot * 4 + 1  # 1, 5, 9
                race_offset_2 = race_offset_1 + 2  # 3, 7, 11
            
            race_num_1 = round_start_race + race_offset_1
            race_num_2 = round_start_race + race_offset_2
            
            # Get the 4 competitors in this group
            group_competitors = [competitors[cid] for cid in group]
            
            # Generate the two races for this double-outing
            # Teammate pairing: in race 1, (0,1) vs (2,3); in race 2, (0,2) vs (1,3)
            # This ensures each person gets 2 unique teammates per round
            c0, c1, c2, c3 = group_competitors
            
            # Determine teammate pairings based on what's already used
            team_pairs = _select_teammate_pairs(c0, c1, c2, c3, used_teammates)
            
            # Race 1
            race1 = Race(
                race_number=race_num_1,
                boat_set=boat_set,
                team_a=Team(team_pairs[0][0], team_pairs[0][1]),
                team_b=Team(team_pairs[1][0], team_pairs[1][1]),
            )
            
            # Race 2
            race2 = Race(
                race_number=race_num_2,
                boat_set=boat_set,
                team_a=Team(team_pairs[2][0], team_pairs[2][1]),
                team_b=Team(team_pairs[3][0], team_pairs[3][1]),
            )
            
            races.append(race1)
            races.append(race2)
            
            # Update used teammates
            for pair in team_pairs:
                used_teammates[pair[0].id].add(pair[1].id)
                used_teammates[pair[1].id].add(pair[0].id)
    
    # Sort races by race number
    races.sort(key=lambda r: r.race_number)
    
    return races


def _compute_round_groups() -> list[list[list[int]]]:
    """
    Compute the groupings of competitors for each round.
    
    Returns a list of 4 rounds, each containing 6 groups of 4 competitor IDs.
    Groups 0-2 are assigned to boat A, groups 3-5 to boat B.
    
    The groupings are designed to ensure:
    1. Each competitor appears in exactly one group per round
    2. Over 4 rounds, no pair of competitors appears in the same group twice
       (enabling 8 unique teammates and 12 unique opponents)
    
    Uses a search-based construction to find 4 mutually orthogonal partitions.
    """
    rounds: list[list[list[int]]] = []
    used_pairs: set[tuple[int, int]] = set()
    
    def to_id(row: int, col: int) -> int:
        return row * 6 + col
    
    def add_round(groups: list[list[int]]) -> None:
        for group in groups:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    pair = (min(group[i], group[j]), max(group[i], group[j]))
                    used_pairs.add(pair)
        rounds.append(groups)
    
    # Round 0: Group by columns - this is always valid as the first round
    round0 = [[to_id(row, col) for row in range(4)] for col in range(6)]
    add_round(round0)
    
    # Round 1: Slope +1 construction (orthogonal to round 0)
    round1 = [[to_id(row, (g + row) % 6) for row in range(4)] for g in range(6)]
    add_round(round1)
    
    # Rounds 2 and 3: Find valid partitions using backtracking
    for _ in range(2):
        next_round = _find_valid_round(list(range(24)), used_pairs)
        add_round(next_round)
    
    return rounds


def _find_valid_round(
    competitors: list[int], 
    forbidden_pairs: set[tuple[int, int]]
) -> list[list[int]]:
    """
    Find a partition of competitors into 6 groups of 4, avoiding forbidden pairs.
    Uses backtracking search.
    """
    def is_valid_group(group: list[int]) -> bool:
        """Check if all pairs in the group are allowed."""
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                pair = (min(group[i], group[j]), max(group[i], group[j]))
                if pair in forbidden_pairs:
                    return False
        return True
    
    def backtrack(remaining: list[int], groups: list[list[int]]) -> list[list[int]] | None:
        if not remaining:
            return groups
        
        if len(remaining) < 4:
            return None
        
        # Try to form a group starting with the first remaining competitor
        first = remaining[0]
        rest = remaining[1:]
        
        # Try all combinations of 3 more competitors from the rest
        from itertools import combinations
        for combo in combinations(rest, 3):
            group = [first] + list(combo)
            if is_valid_group(group):
                new_remaining = [c for c in rest if c not in combo]
                result = backtrack(new_remaining, groups + [group])
                if result is not None:
                    return result
        
        return None
    
    result = backtrack(competitors, [])
    if result is None:
        # Fallback: return a simple partition (will fail validation but indicates issue)
        return [competitors[i:i+4] for i in range(0, 24, 4)]
    return result


def _select_teammate_pairs(
    c0: Competitor, c1: Competitor, c2: Competitor, c3: Competitor,
    used_teammates: dict[int, set[int]]
) -> list[tuple[Competitor, Competitor]]:
    """
    Select teammate pairings for 2 races with 4 competitors.
    
    Returns 4 pairs: [race1_team_a, race1_team_b, race2_team_a, race2_team_b]
    
    Tries to select pairings that don't reuse teammates.
    """
    competitors = [c0, c1, c2, c3]
    
    # All possible ways to partition 4 competitors into 2 pairs for 2 races
    # such that each person gets 2 different teammates
    #
    # Option A: Race1: (0,1) vs (2,3), Race2: (0,2) vs (1,3)
    # Option B: Race1: (0,1) vs (2,3), Race2: (0,3) vs (1,2)
    # Option C: Race1: (0,2) vs (1,3), Race2: (0,1) vs (2,3)
    # Option D: Race1: (0,2) vs (1,3), Race2: (0,3) vs (1,2)
    # Option E: Race1: (0,3) vs (1,2), Race2: (0,1) vs (2,3)
    # Option F: Race1: (0,3) vs (1,2), Race2: (0,2) vs (1,3)
    
    options = [
        [(0,1), (2,3), (0,2), (1,3)],  # Option A
        [(0,1), (2,3), (0,3), (1,2)],  # Option B
        [(0,2), (1,3), (0,1), (2,3)],  # Option C
        [(0,2), (1,3), (0,3), (1,2)],  # Option D
        [(0,3), (1,2), (0,1), (2,3)],  # Option E
        [(0,3), (1,2), (0,2), (1,3)],  # Option F
    ]
    
    # Try to find an option where no teammate pair is already used
    for option in options:
        valid = True
        for i, j in option:
            ci, cj = competitors[i], competitors[j]
            if cj.id in used_teammates[ci.id]:
                valid = False
                break
        
        if valid:
            return [(competitors[i], competitors[j]) for i, j in option]
    
    # If no perfect option, use the first one (will fail validation, 
    # but indicates a design issue we need to fix)
    return [(competitors[i], competitors[j]) for i, j in options[0]]
