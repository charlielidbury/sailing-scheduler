"""Schedule generation logic."""

import random
import time
from itertools import combinations

from .models import (
    NUM_COMPETITORS,
    NUM_RACES,
    BoatSet,
    Competitor,
    Race,
    Schedule,
    Team,
)

# Timeout for schedule generation (seconds)
GENERATION_TIMEOUT = 120


def generate_schedule() -> Schedule:
    """
    Generate a valid sailing competition schedule maximizing visibility and proper double outings.
    
    Uses a chain structure where consecutive races share 2 competitors,
    giving each person ~5 unique others per round instead of 3.
    """
    competitors = [
        Competitor(id=i, name=f"Competitor_{i}")
        for i in range(NUM_COMPETITORS)
    ]
    
    # Try multiple seeds to find a valid schedule
    best_schedule = None
    best_proper_double_outings = 0
    start_time = time.time()
    
    # More seeds for longer schedules (harder to find valid assignments)
    max_seeds = 1000
    valid_found = 0
    
    for seed in range(max_seeds):
        # Check timeout
        if time.time() - start_time > GENERATION_TIMEOUT:
            print(f"Timeout after {seed} seeds ({valid_found} valid), using best schedule found")
            break
        
        # Progress indicator every 100 seeds
        if seed > 0 and seed % 100 == 0:
            print(f"  Tried {seed} seeds, {valid_found} valid, best double outings: {best_proper_double_outings}")
        random.seed(seed)
        races = _try_generate_chain_schedule(competitors)
        if races is not None:
            # Apply opportunistic team swaps to improve double outings
            races = _optimize_double_outings(races)
            
            schedule = Schedule(races=races, competitors=competitors)
            
            # Check opponent diversity
            min_opponents = 24
            for c in competitors:
                opponents: set[int] = set()
                for race in schedule.get_races_for_competitor(c):
                    if c in race.team_a.competitors:
                        for opp in race.team_b.competitors:
                            opponents.add(opp.id)
                    else:
                        for opp in race.team_a.competitors:
                            opponents.add(opp.id)
                min_opponents = min(min_opponents, len(opponents))
            
            if min_opponents < 12:
                continue  # Doesn't meet minimum opponent diversity
            
            # Check for duplicate teammates - allow some tolerance for longer schedules
            # With 16 races and only 23 possible teammates, some overlap may be unavoidable
            from collections import Counter
            max_duplicate_teammates = 0
            total_duplicates = 0
            for c in competitors:
                teammates = schedule.get_teammates_for_competitor(c)
                teammate_counts = Counter(t.id for t in teammates)
                duplicates = sum(count - 1 for count in teammate_counts.values() if count > 1)
                total_duplicates += duplicates
                max_duplicate_teammates = max(max_duplicate_teammates, max(teammate_counts.values()) - 1)
            
            # For 96 races: allow up to 1 repeat per competitor (24 total), 
            # and no competitor should have same teammate more than twice
            max_allowed_total = NUM_COMPETITORS  # 24 total duplicate teammate pairings
            if total_duplicates > max_allowed_total or max_duplicate_teammates > 1:
                continue  # Too many duplicate teammates
            
            valid_found += 1
            
            # Count proper double outings
            proper_double_outings = 0
            for c in competitors:
                comp_races = sorted(schedule.get_races_for_competitor(c), key=lambda r: r.race_number)
                i = 0
                while i < len(comp_races) - 1:
                    r1, r2 = comp_races[i], comp_races[i + 1]
                    if r1.boat_set == r2.boat_set and r2.race_number == r1.race_number + 2:
                        pos1 = _get_boat_position(r1, c)
                        pos2 = _get_boat_position(r2, c)
                        if pos1 == pos2:
                            proper_double_outings += 1
                        i += 2
                    else:
                        i += 1
            
            if proper_double_outings > best_proper_double_outings:
                best_proper_double_outings = proper_double_outings
                best_schedule = schedule
    
    if best_schedule is not None:
        return best_schedule
    
    raise RuntimeError("Could not generate valid schedule")


def _try_generate_chain_schedule(competitors: list[Competitor]) -> list[Race] | None:
    """Attempt to generate a valid chain schedule."""
    races: list[Race] = []
    used_teammates: dict[int, set[int]] = {c.id: set() for c in competitors}
    
    # Track which competitor pairs have been in the same race (could become teammates)
    race_coappearances: dict[int, set[int]] = {c.id: set() for c in competitors}
    
    # Boundary constraint for adjacent races (boat_b last race -> boat_a first race)
    prev_adjacent_boundary: set[int] = set()
    
    # Boundary constraints for consecutive races on SAME boat set
    # Positions 10, 11 race in the last two chain races of a round
    # Positions 0-3 race in the first chain race of a round
    # To prevent 3+ consecutive races, pos 10,11 in round N must not be pos 0-3 in round N+1
    prev_boat_a_boundary: set[int] = set()  # boat_a positions 10, 11 from last round
    prev_boat_b_boundary: set[int] = set()  # boat_b positions 10, 11 from last round
    
    num_rounds = NUM_RACES // 12  # 12 races per round
    for round_num in range(num_rounds):
        round_start = round_num * 12 + 1
        
        # Find valid boat assignments for this round
        boat_a, boat_b = _find_round_assignment(
            used_teammates, 
            race_coappearances, 
            prev_adjacent_boundary,
            prev_boat_a_boundary,
            prev_boat_b_boundary,
            round_num
        )
        
        if boat_a is None:
            return None
        
        boat_a_comps = [competitors[i] for i in boat_a]
        boat_b_comps = [competitors[i] for i in boat_b]
        
        boat_a_nums = [round_start + i * 2 for i in range(6)]
        boat_b_nums = [round_start + 1 + i * 2 for i in range(6)]
        
        # Generate races and track teammate usage
        boat_a_races = _generate_chain_races_careful(
            BoatSet.A, boat_a_nums, boat_a_comps, used_teammates
        )
        boat_b_races = _generate_chain_races_careful(
            BoatSet.B, boat_b_nums, boat_b_comps, used_teammates
        )
        
        if boat_a_races is None or boat_b_races is None:
            return None
        
        # Update co-appearance tracking
        chain = [[0,1,2,3], [2,3,4,5], [4,5,6,7], [6,7,8,9], [8,9,10,11], [10,11,0,1]]
        for group in chain:
            for i in group:
                for j in group:
                    if i != j:
                        race_coappearances[boat_a[i]].add(boat_a[j])
                        race_coappearances[boat_b[i]].add(boat_b[j])
        
        races.extend(boat_a_races)
        races.extend(boat_b_races)
        
        # Update boundaries for next round
        # Adjacent race boundary: boat_b last race positions -> boat_a first race
        prev_adjacent_boundary = {boat_b[0], boat_b[1], boat_b[10], boat_b[11]}
        
        # Same-boat consecutive boundary: ALL positions in last chain race [10, 11, 0, 1]
        # These must not be at positions 0-3 (first chain race) of next round
        prev_boat_a_boundary = {boat_a[0], boat_a[1], boat_a[10], boat_a[11]}
        prev_boat_b_boundary = {boat_b[0], boat_b[1], boat_b[10], boat_b[11]}
    
    races.sort(key=lambda r: r.race_number)
    return races


def _find_round_assignment(
    used_teammates: dict[int, set[int]],
    race_coappearances: dict[int, set[int]],
    prev_adjacent_boundary: set[int],
    prev_boat_a_boundary: set[int],
    prev_boat_b_boundary: set[int],
    round_num: int,
) -> tuple[list[int] | None, list[int] | None]:
    """
    Find valid boat assignments for a round.
    
    Constraints:
    1. 12 competitors per boat
    2. Adjacent race boundary: prev_adjacent_boundary members not in boat_a positions 0-3
       (prevents racing in races N and N+1 which overlap)
    3. Same-boat consecutive boundary: prev_boat_a_boundary not in boat_a positions 0-3,
       prev_boat_b_boundary not in boat_b positions 0-3
       (prevents 3+ consecutive races on same boat set)
    4. Minimize teammate conflicts
    """
    all_ids = list(range(24))
    random.shuffle(all_ids)
    
    # Split into two boats
    boat_a = all_ids[:12]
    boat_b = all_ids[12:]
    
    # Combined boundary for boat_a: both adjacent and same-boat constraints
    boat_a_forbidden = prev_adjacent_boundary | prev_boat_a_boundary
    
    # Combined boundary for boat_b: same-boat constraint
    boat_b_forbidden = prev_boat_b_boundary
    
    # Ensure boat_a positions 0-3 don't have forbidden members
    if boat_a_forbidden:
        forbidden_in_a = [x for x in boat_a if x in boat_a_forbidden]
        safe_in_a = [x for x in boat_a if x not in boat_a_forbidden]
        
        if len(safe_in_a) < 4:
            # Need to swap some forbidden out of boat_a to boat_b
            needed = 4 - len(safe_in_a)
            # Find safe members in boat_b (not forbidden for boat_a)
            safe_in_b = [x for x in boat_b if x not in boat_a_forbidden]
            
            to_move_to_b = forbidden_in_a[:needed]
            to_move_to_a = safe_in_b[:needed]
            
            boat_a = [x for x in boat_a if x not in to_move_to_b] + to_move_to_a
            boat_b = [x for x in boat_b if x not in to_move_to_a] + to_move_to_b
            
            forbidden_in_a = [x for x in boat_a if x in boat_a_forbidden]
            safe_in_a = [x for x in boat_a if x not in boat_a_forbidden]
        
        # Reorder: safe in positions 0-3, forbidden in 4+
        boat_a = safe_in_a[:4] + forbidden_in_a + safe_in_a[4:]
    
    # Ensure boat_b positions 0-3 don't have forbidden members
    if boat_b_forbidden:
        forbidden_in_b = [x for x in boat_b if x in boat_b_forbidden]
        safe_in_b = [x for x in boat_b if x not in boat_b_forbidden]
        
        if len(safe_in_b) < 4:
            # Need to swap some forbidden out of boat_b to boat_a
            needed = 4 - len(safe_in_b)
            # Find safe members in boat_a that can go to boat_b
            # (must not be in positions 0-3 of boat_a if boat_a_forbidden)
            available_in_a = boat_a[4:] if boat_a_forbidden else boat_a
            safe_for_b = [x for x in available_in_a if x not in boat_b_forbidden]
            
            to_move_to_a = forbidden_in_b[:needed]
            to_move_to_b = safe_for_b[:needed]
            
            # Update boats
            new_boat_b = [x for x in boat_b if x not in to_move_to_a] + to_move_to_b
            new_boat_a = [x for x in boat_a if x not in to_move_to_b] + to_move_to_a
            
            # Re-apply boat_a constraint
            if boat_a_forbidden:
                forbidden_in_a = [x for x in new_boat_a if x in boat_a_forbidden]
                safe_in_a = [x for x in new_boat_a if x not in boat_a_forbidden]
                boat_a = safe_in_a[:4] + forbidden_in_a + safe_in_a[4:]
            else:
                boat_a = new_boat_a
            
            forbidden_in_b = [x for x in new_boat_b if x in boat_b_forbidden]
            safe_in_b = [x for x in new_boat_b if x not in boat_b_forbidden]
            boat_b = new_boat_b
        
        # Reorder boat_b: safe in positions 0-3, forbidden in 4+
        boat_b = safe_in_b[:4] + forbidden_in_b + safe_in_b[4:]
    
    # Verify constraints
    if boat_a_forbidden:
        assert not any(boat_a[i] in boat_a_forbidden for i in range(4)), \
            f"Boat A boundary violated: positions 0-3 = {boat_a[:4]}, forbidden = {boat_a_forbidden}"
    if boat_b_forbidden:
        assert not any(boat_b[i] in boat_b_forbidden for i in range(4)), \
            f"Boat B boundary violated: positions 0-3 = {boat_b[:4]}, forbidden = {boat_b_forbidden}"
    
    # Optimize ordering to minimize teammate conflicts
    chain = [[0,1,2,3], [2,3,4,5], [4,5,6,7], [6,7,8,9], [8,9,10,11], [10,11,0,1]]
    
    def count_conflicts(ordering: list[int]) -> int:
        conflicts = 0
        for group in chain:
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    c1, c2 = ordering[group[i]], ordering[group[j]]
                    if c2 in used_teammates[c1]:
                        conflicts += 1
        return conflicts
    
    def is_valid_a(ordering: list[int]) -> bool:
        if not boat_a_forbidden:
            return True
        return not any(ordering[i] in boat_a_forbidden for i in range(4))
    
    def is_valid_b(ordering: list[int]) -> bool:
        if not boat_b_forbidden:
            return True
        return not any(ordering[i] in boat_b_forbidden for i in range(4))
    
    # Optimize boat_a (keeping boundary constraint)
    best_a = boat_a[:]
    best_a_conflicts = count_conflicts(best_a)
    
    for _ in range(1000):
        new_a = best_a[:]
        # Only swap within safe zone (0-3) or within rest (4-11) to maintain constraint
        if boat_a_forbidden:
            if random.random() < 0.3:
                i, j = random.sample(range(4), 2)
            else:
                i, j = random.sample(range(4, 12), 2)
        else:
            i, j = random.sample(range(12), 2)
        new_a[i], new_a[j] = new_a[j], new_a[i]
        
        if is_valid_a(new_a):
            new_conflicts = count_conflicts(new_a)
            if new_conflicts < best_a_conflicts:
                best_a = new_a
                best_a_conflicts = new_conflicts
    
    # Optimize boat_b (keeping boundary constraint)
    best_b = boat_b[:]
    best_b_conflicts = count_conflicts(best_b)
    
    for _ in range(1000):
        new_b = best_b[:]
        if boat_b_forbidden:
            if random.random() < 0.3:
                i, j = random.sample(range(4), 2)
            else:
                i, j = random.sample(range(4, 12), 2)
        else:
            i, j = random.sample(range(12), 2)
        new_b[i], new_b[j] = new_b[j], new_b[i]
        
        if is_valid_b(new_b):
            new_conflicts = count_conflicts(new_b)
            if new_conflicts < best_b_conflicts:
                best_b = new_b
                best_b_conflicts = new_conflicts
    
    return best_a, best_b


def _generate_chain_races_careful(
    boat_set: BoatSet,
    race_numbers: list[int],
    boat_competitors: list[Competitor],
    used_teammates: dict[int, set[int]],
) -> list[Race] | None:
    """Generate chain races with careful teammate selection."""
    races: list[Race] = []
    
    chain = [
        [0, 1, 2, 3],
        [2, 3, 4, 5],
        [4, 5, 6, 7],
        [6, 7, 8, 9],
        [8, 9, 10, 11],
        [10, 11, 0, 1],
    ]
    
    for race_idx, race_num in enumerate(race_numbers):
        indices = chain[race_idx]
        race_competitors = [boat_competitors[i] for i in indices]
        
        team_a, team_b = _form_teams_optimally(race_competitors, used_teammates)
        
        race = Race(
            race_number=race_num,
            boat_set=boat_set,
            team_a=team_a,
            team_b=team_b,
        )
        races.append(race)
        
        # Update teammates
        for c in team_a.competitors:
            for other in team_a.competitors:
                if c.id != other.id:
                    used_teammates[c.id].add(other.id)
        for c in team_b.competitors:
            for other in team_b.competitors:
                if c.id != other.id:
                    used_teammates[c.id].add(other.id)
    
    return races


def _form_teams_optimally(
    race_competitors: list[Competitor],
    used_teammates: dict[int, set[int]],
) -> tuple[Team, Team] | None:
    """
    Form teams avoiding duplicate teammates.
    
    Returns None if no valid formation exists (all options create duplicates).
    """
    c0, c1, c2, c3 = race_competitors
    
    formations = [
        ((c0, c1), (c2, c3)),
        ((c0, c2), (c1, c3)),
        ((c0, c3), (c1, c2)),
    ]
    
    best_formation = None
    best_score = float('inf')
    
    for (a1, a2), (b1, b2) in formations:
        score = 0
        if a2.id in used_teammates[a1.id]:
            score += 1
        if b2.id in used_teammates[b1.id]:
            score += 1
        
        if score < best_score:
            best_score = score
            best_formation = ((a1, a2), (b1, b2))
    
    if best_formation is None:
        return None
    
    (a1, a2), (b1, b2) = best_formation
    return Team(a1, a2), Team(b1, b2)


def _get_boat_position(race: Race, competitor: Competitor) -> str | None:
    """
    Get the boat position (column) of a competitor in a race.
    
    Returns one of: 'a1' (team_a pos 7), 'a2' (team_a pos 8), 
                    'b1' (team_b pos 10), 'b2' (team_b pos 11)
    Or None if competitor not in race.
    """
    if race.team_a.competitor1 == competitor:
        return 'a1'
    elif race.team_a.competitor2 == competitor:
        return 'a2'
    elif race.team_b.competitor1 == competitor:
        return 'b1'
    elif race.team_b.competitor2 == competitor:
        return 'b2'
    return None


def _swap_within_team_a(race: Race) -> Race:
    """Swap competitor1 and competitor2 within team_a."""
    new_team_a = Team(race.team_a.competitor2, race.team_a.competitor1)
    return Race(
        race_number=race.race_number,
        boat_set=race.boat_set,
        team_a=new_team_a,
        team_b=race.team_b,
    )


def _swap_within_team_b(race: Race) -> Race:
    """Swap competitor1 and competitor2 within team_b."""
    new_team_b = Team(race.team_b.competitor2, race.team_b.competitor1)
    return Race(
        race_number=race.race_number,
        boat_set=race.boat_set,
        team_a=race.team_a,
        team_b=new_team_b,
    )


def _count_total_aligned(races_by_boat: dict[BoatSet, list[Race]]) -> int:
    """Count total aligned double outings across all race pairs."""
    total = 0
    for boat_set in [BoatSet.A, BoatSet.B]:
        boat_races = races_by_boat[boat_set]
        for i in range(len(boat_races) - 1):
            race1, race2 = boat_races[i], boat_races[i + 1]
            c1_all = set(race1.all_competitors)
            c2_all = set(race2.all_competitors)
            shared = list(c1_all & c2_all)
            if len(shared) == 2:
                for comp in shared:
                    if _get_boat_position(race1, comp) == _get_boat_position(race2, comp):
                        total += 1
    return total


def _optimize_double_outings(races: list[Race]) -> list[Race]:
    """
    Opportunistically swap boat positions within teams to improve double outings.
    
    A proper double-outing requires staying in the SAME boat position (column)
    across races N and N+2. This function swaps competitor1/competitor2 within
    teams to align boat positions where possible.
    
    Uses multiple passes to find improvements that might only become apparent
    after other swaps have been made.
    """
    # Group races by boat set
    races_by_boat: dict[BoatSet, list[Race]] = {BoatSet.A: [], BoatSet.B: []}
    for race in races:
        races_by_boat[race.boat_set].append(race)
    
    for boat_set in [BoatSet.A, BoatSet.B]:
        races_by_boat[boat_set] = sorted(races_by_boat[boat_set], key=lambda r: r.race_number)
    
    # Multiple passes to find improvements
    for _ in range(5):  # Up to 5 passes
        improved = False
        
        for boat_set in [BoatSet.A, BoatSet.B]:
            boat_races = races_by_boat[boat_set]
            
            for i in range(len(boat_races) - 1):
                race1 = races_by_boat[boat_set][i]
                race2 = races_by_boat[boat_set][i + 1]
                
                # Find competitors in both races
                c1_all = set(race1.all_competitors)
                c2_all = set(race2.all_competitors)
                shared = list(c1_all & c2_all)
                
                if len(shared) != 2:
                    continue
                
                comp1, comp2 = shared[0], shared[1]
                pos1_r1 = _get_boat_position(race1, comp1)
                pos1_r2 = _get_boat_position(race2, comp1)
                pos2_r1 = _get_boat_position(race1, comp2)
                pos2_r2 = _get_boat_position(race2, comp2)
                
                current_aligned = (pos1_r1 == pos1_r2) + (pos2_r1 == pos2_r2)
                
                if current_aligned == 2:
                    continue
                
                # Try all swaps in BOTH races
                best_race1, best_race2 = race1, race2
                best_aligned = current_aligned
                
                # Generate all variants of race1
                race1_variants = [
                    race1,
                    _swap_within_team_a(race1),
                    _swap_within_team_b(race1),
                    _swap_within_team_b(_swap_within_team_a(race1)),
                ]
                
                # Generate all variants of race2
                race2_variants = [
                    race2,
                    _swap_within_team_a(race2),
                    _swap_within_team_b(race2),
                    _swap_within_team_b(_swap_within_team_a(race2)),
                ]
                
                # Try all combinations
                for r1_var in race1_variants:
                    for r2_var in race2_variants:
                        new_pos1_r1 = _get_boat_position(r1_var, comp1)
                        new_pos1_r2 = _get_boat_position(r2_var, comp1)
                        new_pos2_r1 = _get_boat_position(r1_var, comp2)
                        new_pos2_r2 = _get_boat_position(r2_var, comp2)
                        
                        aligned = (new_pos1_r1 == new_pos1_r2) + (new_pos2_r1 == new_pos2_r2)
                        if aligned > best_aligned:
                            best_aligned = aligned
                            best_race1 = r1_var
                            best_race2 = r2_var
                
                if best_aligned > current_aligned:
                    races_by_boat[boat_set][i] = best_race1
                    races_by_boat[boat_set][i + 1] = best_race2
                    improved = True
        
        if not improved:
            break
    
    # Reconstruct races list
    result = races_by_boat[BoatSet.A] + races_by_boat[BoatSet.B]
    result.sort(key=lambda r: r.race_number)
    return result
