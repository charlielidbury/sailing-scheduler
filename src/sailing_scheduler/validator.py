"""
Schedule validation logic.

These checks verify that a generated schedule satisfies all the constraints
defined in the README.md. They can be run at test time or after generating
any schedule.
"""

from collections import Counter
from dataclasses import dataclass

from .models import (
    NUM_COMPETITORS,
    NUM_RACES,
    RACES_PER_COMPETITOR,
    BoatSet,
    Competitor,
    Schedule,
)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str


@dataclass
class ValidationReport:
    """Full validation report for a schedule."""
    results: dict[str, ValidationResult]
    
    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results.values())
    
    def __str__(self) -> str:
        lines = ["Schedule Validation Report", "=" * 40]
        for name, result in self.results.items():
            status = "✓ PASS" if result.passed else "✗ FAIL"
            lines.append(f"{status}: {name}")
            if not result.passed:
                lines.append(f"       {result.message}")
        lines.append("=" * 40)
        lines.append(f"Overall: {'PASSED' if self.all_passed else 'FAILED'}")
        return "\n".join(lines)


def check_correct_number_of_competitors(schedule: Schedule) -> ValidationResult:
    """Schedule should have exactly 24 competitors."""
    count = len(schedule.competitors)
    passed = count == NUM_COMPETITORS
    return ValidationResult(
        passed=passed,
        message=f"Expected {NUM_COMPETITORS} competitors, got {count}"
    )


def check_correct_number_of_races(schedule: Schedule) -> ValidationResult:
    """Schedule should have exactly 48 races."""
    count = len(schedule.races)
    passed = count == NUM_RACES
    return ValidationResult(
        passed=passed,
        message=f"Expected {NUM_RACES} races, got {count}"
    )


def check_boat_sets_alternate(schedule: Schedule) -> ValidationResult:
    """Boat sets should alternate between races (A, B, A, B, ...)."""
    errors = []
    for i, race in enumerate(schedule.races):
        expected_set = BoatSet.A if i % 2 == 0 else BoatSet.B
        if race.boat_set != expected_set:
            errors.append(
                f"Race {race.race_number}: expected {expected_set}, got {race.boat_set}"
            )
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def check_race_numbers_sequential(schedule: Schedule) -> ValidationResult:
    """Race numbers should be sequential starting from 1."""
    race_numbers = [race.race_number for race in schedule.races]
    expected = list(range(1, NUM_RACES + 1))
    passed = race_numbers == expected
    return ValidationResult(
        passed=passed,
        message=f"Race numbers are not sequential 1-{NUM_RACES}"
    )


def check_each_race_has_four_unique_competitors(schedule: Schedule) -> ValidationResult:
    """Each race should have exactly 4 unique competitors (2 per team)."""
    errors = []
    for race in schedule.races:
        count = len(race.all_competitors)
        if count != 4:
            errors.append(f"Race {race.race_number} has {count} competitors")
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def check_no_adjacent_races(schedule: Schedule) -> ValidationResult:
    """
    Requirement 1: No competitor should race in consecutive race numbers.
    
    Race N and race N+1 overlap in time, so a competitor cannot be in both.
    """
    errors = []
    for competitor in schedule.competitors:
        race_numbers = schedule.get_race_numbers_for_competitor(competitor)
        
        for i in range(len(race_numbers) - 1):
            current_race = race_numbers[i]
            next_race = race_numbers[i + 1]
            if next_race == current_race + 1:
                errors.append(
                    f"{competitor.name} in adjacent races {current_race} and {next_race}"
                )
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def check_exactly_eight_races(schedule: Schedule) -> ValidationResult:
    """
    Requirement 2: Each competitor partakes in exactly 8 races.
    """
    errors = []
    for competitor in schedule.competitors:
        race_count = len(schedule.get_races_for_competitor(competitor))
        if race_count != RACES_PER_COMPETITOR:
            errors.append(f"{competitor.name} has {race_count} races")
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def check_unique_teammates(schedule: Schedule) -> ValidationResult:
    """
    Requirement 3: Each competitor must not be scheduled to race with 
    the same teammate more than once.
    """
    errors = []
    for competitor in schedule.competitors:
        teammates = schedule.get_teammates_for_competitor(competitor)
        teammate_counts = Counter(teammates)
        
        duplicates = {
            tm.name: count 
            for tm, count in teammate_counts.items() 
            if count > 1
        }
        
        if duplicates:
            errors.append(f"{competitor.name} has duplicate teammates: {duplicates}")
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def _count_outings(race_numbers: list[int]) -> tuple[int, int]:
    """
    Count single-race and double-race outings.
    
    An outing is a contiguous sequence where each race is exactly 2 apart.
    For example: [1, 3] is one double-race outing.
    
    Returns:
        (single_race_outings, double_race_outings)
    """
    if not race_numbers:
        return (0, 0)
    
    single_outings = 0
    double_outings = 0
    
    i = 0
    while i < len(race_numbers):
        # Check if this race is part of a pair (N and N+2)
        if i + 1 < len(race_numbers) and race_numbers[i + 1] == race_numbers[i] + 2:
            double_outings += 1
            i += 2  # Skip the next race as it's part of this outing
        else:
            single_outings += 1
            i += 1
    
    return (single_outings, double_outings)


def check_two_race_outings(schedule: Schedule) -> ValidationResult:
    """
    Requirement 4 & 5: Prefer two-race-per-outing pattern and minimize single outings.
    
    Due to concurrent races, "two races in a row" means race N followed by race N+2.
    """
    total_single_outings = 0
    total_double_outings = 0
    
    for competitor in schedule.competitors:
        race_numbers = schedule.get_race_numbers_for_competitor(competitor)
        single, double = _count_outings(race_numbers)
        total_single_outings += single
        total_double_outings += double
    
    # Ideal: 24 competitors × 4 double outings = 96 double outings, 0 single
    ideal_double_outings = NUM_COMPETITORS * (RACES_PER_COMPETITOR // 2)
    
    # Allow some tolerance - max 2 single outings per competitor on average
    max_acceptable_single_outings = NUM_COMPETITORS * 2
    passed = total_single_outings <= max_acceptable_single_outings
    
    return ValidationResult(
        passed=passed,
        message=(
            f"Single outings: {total_single_outings} (max acceptable: {max_acceptable_single_outings}), "
            f"Double outings: {total_double_outings} (ideal: {ideal_double_outings})"
        )
    )


def check_schedule_balance(schedule: Schedule) -> ValidationResult:
    """
    Requirement 6: The schedule must be interruptible.
    
    At regular intervals, all competitors should have raced similar amounts.
    """
    checkpoints = [12, 24, 36, 48]
    errors = []
    max_acceptable_spread = 4
    
    for checkpoint in checkpoints:
        if checkpoint > len(schedule.races):
            continue
            
        races_so_far = schedule.races[:checkpoint]
        
        # Count races per competitor up to this point
        race_counts: dict[int, int] = {c.id: 0 for c in schedule.competitors}
        for race in races_so_far:
            for competitor in race.all_competitors:
                race_counts[competitor.id] += 1
        
        counts = list(race_counts.values())
        if not counts:
            continue
            
        min_races = min(counts)
        max_races = max(counts)
        spread = max_races - min_races
        
        if spread > max_acceptable_spread:
            errors.append(f"Race {checkpoint}: spread={spread} (max {max_acceptable_spread})")
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors)
    )


def check_round_structure(schedule: Schedule) -> ValidationResult:
    """
    Requirement 6: Schedule should have round structure.
    
    Each competitor should race exactly twice per round (12 races per round).
    """
    races_per_round = 12
    num_rounds = NUM_RACES // races_per_round
    errors = []
    
    for round_num in range(num_rounds):
        start_idx = round_num * races_per_round
        end_idx = start_idx + races_per_round
        
        if end_idx > len(schedule.races):
            break
            
        round_races = schedule.races[start_idx:end_idx]
        
        # Count races per competitor in this round
        race_counts: dict[int, int] = {c.id: 0 for c in schedule.competitors}
        for race in round_races:
            for competitor in race.all_competitors:
                race_counts[competitor.id] += 1
        
        # Each competitor should race exactly twice per round
        for competitor in schedule.competitors:
            count = race_counts[competitor.id]
            if count != 2:
                errors.append(
                    f"Round {round_num + 1}: {competitor.name} has {count} races (expected 2)"
                )
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def check_opponent_diversity(schedule: Schedule) -> ValidationResult:
    """
    Additional: Each competitor should face a reasonable variety of opponents.
    
    With 8 races and 2 opponents per race, each competitor faces 16 opponent slots.
    Should face at least 12 unique opponents.
    """
    errors = []
    min_unique_opponents = 12
    
    for competitor in schedule.competitors:
        opponents: list[Competitor] = []
        for race in schedule.get_races_for_competitor(competitor):
            if competitor in race.team_a.competitors:
                opponents.extend(race.team_b.competitors)
            else:
                opponents.extend(race.team_a.competitors)
        
        unique_opponents = len(set(opponents))
        
        if unique_opponents < min_unique_opponents and len(opponents) > 0:
            errors.append(
                f"{competitor.name} faced {unique_opponents} unique opponents (min {min_unique_opponents})"
            )
    
    return ValidationResult(
        passed=len(errors) == 0,
        message="; ".join(errors[:3]) + (f" (+{len(errors)-3} more)" if len(errors) > 3 else "")
    )


def validate_schedule(schedule: Schedule) -> ValidationReport:
    """
    Run all validation checks on a schedule.
    
    Returns a ValidationReport with results for each check.
    """
    checks = {
        "correct_number_of_competitors": check_correct_number_of_competitors,
        "correct_number_of_races": check_correct_number_of_races,
        "boat_sets_alternate": check_boat_sets_alternate,
        "race_numbers_sequential": check_race_numbers_sequential,
        "each_race_has_four_competitors": check_each_race_has_four_unique_competitors,
        "req1_no_adjacent_races": check_no_adjacent_races,
        "req2_exactly_eight_races": check_exactly_eight_races,
        "req3_unique_teammates": check_unique_teammates,
        "req4_5_two_race_outings": check_two_race_outings,
        "req6_schedule_balance": check_schedule_balance,
        "req6_round_structure": check_round_structure,
        "opponent_diversity": check_opponent_diversity,
    }
    
    results = {name: check(schedule) for name, check in checks.items()}
    return ValidationReport(results=results)

