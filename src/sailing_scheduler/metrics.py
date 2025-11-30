"""Schedule quality metrics for optimization."""

from dataclasses import dataclass

from .models import Competitor, Schedule


@dataclass
class ScheduleMetrics:
    """Quality metrics for a schedule."""
    
    # Visibility: unique competitors seen (teammates + opponents)
    min_visibility: int
    max_visibility: int
    avg_visibility: float
    total_visibility: int
    
    # Outings
    total_single_outings: int
    total_potential_double_outings: int  # Races N and N+2 on same boat set
    total_proper_double_outings: int     # Same boat position (column)
    
    # Teammates
    duplicate_teammates: int  # Should be 0
    
    # Opponents
    min_unique_opponents: int
    max_unique_opponents: int
    
    def __str__(self) -> str:
        lines = [
            "Schedule Quality Metrics",
            "=" * 40,
            f"Visibility (unique others seen per competitor):",
            f"  Min: {self.min_visibility}, Max: {self.max_visibility}, Avg: {self.avg_visibility:.1f}",
            f"  Total across all competitors: {self.total_visibility}",
            f"Outings:",
            f"  Single outings: {self.total_single_outings}",
            f"  Potential double outings: {self.total_potential_double_outings}",
            f"  Proper double outings (same boat): {self.total_proper_double_outings}",
            f"Teammates:",
            f"  Duplicate teammates: {self.duplicate_teammates} {'✓' if self.duplicate_teammates == 0 else '✗'}",
            f"Opponents:",
            f"  Unique opponents: min={self.min_unique_opponents}, max={self.max_unique_opponents}",
            "=" * 40,
        ]
        return "\n".join(lines)


def compute_visibility(schedule: Schedule, competitor: Competitor) -> int:
    """
    Compute how many unique other competitors this competitor 'sees'.
    
    A competitor 'sees' everyone they race with or against.
    """
    seen: set[int] = set()
    for race in schedule.get_races_for_competitor(competitor):
        for c in race.all_competitors:
            if c.id != competitor.id:
                seen.add(c.id)
    return len(seen)


def compute_unique_opponents(schedule: Schedule, competitor: Competitor) -> int:
    """Count unique opponents faced by a competitor."""
    opponents: set[int] = set()
    for race in schedule.get_races_for_competitor(competitor):
        if competitor in race.team_a.competitors:
            for c in race.team_b.competitors:
                opponents.add(c.id)
        else:
            for c in race.team_a.competitors:
                opponents.add(c.id)
    return len(opponents)


def count_duplicate_teammates(schedule: Schedule, competitor: Competitor) -> int:
    """Count how many times a teammate appears more than once."""
    from collections import Counter
    teammates = schedule.get_teammates_for_competitor(competitor)
    counts = Counter(t.id for t in teammates)
    return sum(c - 1 for c in counts.values() if c > 1)


def _get_boat_position(race, competitor) -> str | None:
    """
    Get the boat position (column) of a competitor in a race.
    
    Returns one of: 'a1', 'a2', 'b1', 'b2' or None.
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


def count_outings(race_numbers: list[int]) -> tuple[int, int]:
    """
    Count single and potential double outings (by race numbers only).
    
    Returns (single_outings, potential_double_outings).
    """
    if not race_numbers:
        return (0, 0)
    
    single = 0
    double = 0
    i = 0
    
    while i < len(race_numbers):
        if i + 1 < len(race_numbers) and race_numbers[i + 1] == race_numbers[i] + 2:
            double += 1
            i += 2
        else:
            single += 1
            i += 1
    
    return (single, double)


def count_proper_double_outings(schedule, competitor) -> int:
    """
    Count proper double outings (same boat position) for a competitor.
    
    A proper double outing is when a competitor races in N and N+2 on the
    same boat set AND stays in the same boat position (column).
    """
    races = sorted(schedule.get_races_for_competitor(competitor), key=lambda r: r.race_number)
    proper_count = 0
    
    i = 0
    while i < len(races) - 1:
        r1, r2 = races[i], races[i + 1]
        
        # Check if this is a potential double outing
        if r1.boat_set == r2.boat_set and r2.race_number == r1.race_number + 2:
            # Check if same boat position
            pos1 = _get_boat_position(r1, competitor)
            pos2 = _get_boat_position(r2, competitor)
            if pos1 == pos2:
                proper_count += 1
            i += 2  # Skip both races of this outing
        else:
            i += 1
    
    return proper_count


def calculate_metrics(schedule: Schedule) -> ScheduleMetrics:
    """Calculate all quality metrics for a schedule."""
    visibilities = []
    unique_opponents_list = []
    total_single = 0
    total_potential_double = 0
    total_proper_double = 0
    total_dup_teammates = 0
    
    for competitor in schedule.competitors:
        # Visibility
        vis = compute_visibility(schedule, competitor)
        visibilities.append(vis)
        
        # Opponents
        opp = compute_unique_opponents(schedule, competitor)
        unique_opponents_list.append(opp)
        
        # Outings
        race_nums = schedule.get_race_numbers_for_competitor(competitor)
        single, potential_double = count_outings(race_nums)
        proper_double = count_proper_double_outings(schedule, competitor)
        total_single += single
        total_potential_double += potential_double
        total_proper_double += proper_double
        
        # Duplicate teammates
        dup = count_duplicate_teammates(schedule, competitor)
        total_dup_teammates += dup
    
    return ScheduleMetrics(
        min_visibility=min(visibilities),
        max_visibility=max(visibilities),
        avg_visibility=sum(visibilities) / len(visibilities),
        total_visibility=sum(visibilities),
        total_single_outings=total_single,
        total_potential_double_outings=total_potential_double,
        total_proper_double_outings=total_proper_double,
        duplicate_teammates=total_dup_teammates,
        min_unique_opponents=min(unique_opponents_list),
        max_unique_opponents=max(unique_opponents_list),
    )

