"""
Test that the schedule generator produces a valid schedule.
"""

from sailing_scheduler import generate_schedule
from sailing_scheduler.validator import validate_schedule


def test_generated_schedule_is_valid() -> None:
    """Generate a schedule and verify all requirements are met."""
    schedule = generate_schedule()
    report = validate_schedule(schedule)
    
    # Print the report for visibility
    print(f"\n{report}")
    
    # Assert each check individually for clear test output
    for name, result in report.results.items():
        assert result.passed, f"{name}: {result.message}"
