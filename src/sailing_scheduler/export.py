"""Export schedule to various formats."""

from .models import BoatSet, Schedule


def schedule_to_tsv(schedule: Schedule) -> str:
    """
    Export schedule to TSV format for spreadsheet import.
    
    Format:
    - Cambridge Pink and Black Stripe (Boat Set A)
    - RHS Green Circle/Black Diamond (Boat Set B)
    
    Each race fills in the appropriate columns based on which boat set is used.
    """
    lines: list[str] = []
    
    # Header row 1: Boat set names (spanning columns)
    lines.append("\tCambridge Pink and Black Stripe\t\t\t\tRHS Green Circle/Black Diamond\t\t\t")
    
    # Header row 2: Boat names with positions
    lines.append("Race\tPink(7, 8)\t\tBlack Stripe(10, 11)\t\tGreen Circle(7, 8)\t\tBlack Diamond(10, 11)\t")
    
    # Race rows
    for race in schedule.races:
        # Get competitor names
        team_a_c1 = race.team_a.competitor1.name
        team_a_c2 = race.team_a.competitor2.name
        team_b_c1 = race.team_b.competitor1.name
        team_b_c2 = race.team_b.competitor2.name
        
        if race.boat_set == BoatSet.A:
            # Cambridge boats (Pink and Black Stripe)
            # Team A in Pink, Team B in Black Stripe
            row = f"{race.race_number}\t{team_a_c1}\t{team_a_c2}\t{team_b_c1}\t{team_b_c2}\t\t\t\t"
        else:
            # RHS boats (Green Circle and Black Diamond)
            # Team A in Green Circle, Team B in Black Diamond
            row = f"{race.race_number}\t\t\t\t\t{team_a_c1}\t{team_a_c2}\t{team_b_c1}\t{team_b_c2}"
        
        lines.append(row)
    
    return "\n".join(lines)


def export_schedule_tsv(schedule: Schedule, filepath: str) -> None:
    """Export schedule to a TSV file."""
    tsv_content = schedule_to_tsv(schedule)
    with open(filepath, "w") as f:
        f.write(tsv_content)

