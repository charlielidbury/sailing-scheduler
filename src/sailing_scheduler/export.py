"""Export schedule to various formats."""

from collections import defaultdict

from .models import BoatSet, Schedule, NUM_COMPETITORS


def _short_name(name: str) -> str:
    """Strip 'Competitor_' prefix from name."""
    if name.startswith("Competitor_"):
        return name[len("Competitor_"):]
    return name


def schedule_to_tsv(schedule: Schedule) -> str:
    """
    Export schedule to TSV format for spreadsheet import.
    
    Format:
    - Cambridge Pink and Black Stripe (Boat Set A)
    - RHS Green Circle/Black Diamond (Boat Set B)
    - Min/Max columns showing race count balance at each point
    
    Each race fills in the appropriate columns based on which boat set is used.
    """
    lines: list[str] = []
    
    # Header row 1: Boat set names (spanning columns)
    lines.append("\tCambridge Pink and Black Stripe\t\t\t\tRHS Green Circle/Black Diamond\t\t\t\tBalance")
    
    # Header row 2: Boat names with positions
    lines.append("Race\tPink(7, 8)\t\tBlack Stripe(10, 11)\t\tGreen Circle(7, 8)\t\tBlack Diamond(10, 11)\t\tMin\tMax")
    
    # Track cumulative race counts for balance columns
    race_counts: dict[int, int] = {c.id: 0 for c in schedule.competitors}
    
    # Race rows
    for race in schedule.races:
        # Update race counts for competitors in this race
        for competitor in race.all_competitors:
            race_counts[competitor.id] += 1
        
        # Calculate min/max at this point
        counts = list(race_counts.values())
        min_races = min(counts)
        max_races = max(counts)
        
        # Get competitor names (without prefix)
        team_a_c1 = _short_name(race.team_a.competitor1.name)
        team_a_c2 = _short_name(race.team_a.competitor2.name)
        team_b_c1 = _short_name(race.team_b.competitor1.name)
        team_b_c2 = _short_name(race.team_b.competitor2.name)
        
        if race.boat_set == BoatSet.A:
            # Cambridge boats (Pink and Black Stripe)
            # Team A in Pink, Team B in Black Stripe
            row = f"{race.race_number}\t{team_a_c1}\t{team_a_c2}\t{team_b_c1}\t{team_b_c2}\t\t\t\t\t{min_races}\t{max_races}"
        else:
            # RHS boats (Green Circle and Black Diamond)
            # Team A in Green Circle, Team B in Black Diamond
            row = f"{race.race_number}\t\t\t\t\t{team_a_c1}\t{team_a_c2}\t{team_b_c1}\t{team_b_c2}\t{min_races}\t{max_races}"
        
        lines.append(row)
    
    return "\n".join(lines)


def export_schedule_tsv(schedule: Schedule, filepath: str) -> None:
    """Export schedule to a TSV file."""
    tsv_content = schedule_to_tsv(schedule)
    with open(filepath, "w") as f:
        f.write(tsv_content)


def sightings_table_to_tsv(schedule: Schedule) -> str:
    """
    Generate a two-way table showing how many times each competitor sees each other.
    
    Each cell shows X/Y where:
    - X = number of times they were teammates
    - Y = number of times they were opponents
    """
    # Initialize counts
    teammate_count: dict[tuple[int, int], int] = defaultdict(int)
    opponent_count: dict[tuple[int, int], int] = defaultdict(int)
    
    for race in schedule.races:
        # Teammates: within same team
        t_a = list(race.team_a.competitors)
        t_b = list(race.team_b.competitors)
        
        # Team A teammates
        for i, c1 in enumerate(t_a):
            for c2 in t_a[i+1:]:
                pair = (min(c1.id, c2.id), max(c1.id, c2.id))
                teammate_count[pair] += 1
        
        # Team B teammates
        for i, c1 in enumerate(t_b):
            for c2 in t_b[i+1:]:
                pair = (min(c1.id, c2.id), max(c1.id, c2.id))
                teammate_count[pair] += 1
        
        # Opponents: across teams
        for c1 in t_a:
            for c2 in t_b:
                pair = (min(c1.id, c2.id), max(c1.id, c2.id))
                opponent_count[pair] += 1
    
    # Build table
    lines: list[str] = []
    
    # Header row
    header = [""] + [str(i) for i in range(NUM_COMPETITORS)]
    lines.append("\t".join(header))
    
    # Data rows
    for i in range(NUM_COMPETITORS):
        row = [str(i)]
        for j in range(NUM_COMPETITORS):
            if i == j:
                row.append("-")
            else:
                pair = (min(i, j), max(i, j))
                t = teammate_count[pair]
                o = opponent_count[pair]
                row.append(f"{t}/{o}")
        lines.append("\t".join(row))
    
    return "\n".join(lines)


def export_sightings_table(schedule: Schedule, filepath: str) -> None:
    """Export sightings table to a TSV file."""
    tsv_content = sightings_table_to_tsv(schedule)
    with open(filepath, "w") as f:
        f.write(tsv_content)


def _get_boat_position(race, competitor) -> str | None:
    """
    Get the boat position (column) of a competitor in a race.
    
    Returns one of: 'a1' (team_a pos 7/7), 'a2' (team_a pos 8/8), 
                    'b1' (team_b pos 10/10), 'b2' (team_b pos 11/11)
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


def double_changeover_table_to_tsv(schedule: Schedule) -> str:
    """
    Generate a table showing double outings on a per-competitor basis.
    
    A proper double outing is when a competitor stays in the SAME boat position
    (same column) across races N and N+2. This tracks:
    - Same boat: stayed in exact same boat position (proper double outing)
    - Switched boat: in both races but had to change boats
    """
    lines: list[str] = []
    
    # Track per-competitor stats: (race1, race2, same_boat: bool)
    competitor_stats: dict[int, list[tuple[int, int, bool]]] = {i: [] for i in range(NUM_COMPETITORS)}
    
    for c in schedule.competitors:
        # Get this competitor's races in order
        races = sorted(schedule.get_races_for_competitor(c), key=lambda r: r.race_number)
        
        # Find consecutive races on same boat set (race N and N+2)
        for i in range(len(races) - 1):
            r1, r2 = races[i], races[i + 1]
            
            # Check if this is a potential double outing (same boat set, races differ by 2)
            if r1.boat_set == r2.boat_set and r2.race_number == r1.race_number + 2:
                # Check if they're in the same boat position
                pos1 = _get_boat_position(r1, c)
                pos2 = _get_boat_position(r2, c)
                same_boat = (pos1 == pos2)
                
                competitor_stats[c.id].append((r1.race_number, r2.race_number, same_boat))
    
    # Summary per competitor
    lines.append("Double Outing Summary (Per Competitor)")
    lines.append("")
    lines.append("A proper double outing means staying in the SAME boat (column) across races N and N+2.")
    lines.append("")
    lines.append("Competitor\tPotential Double Outings\tSame Boat (proper)\tSwitched Boat")
    
    total_potential = 0
    total_same_boat = 0
    total_switched = 0
    
    for c_id in range(NUM_COMPETITORS):
        outings = competitor_stats[c_id]
        potential = len(outings)
        same_boat = sum(1 for _, _, same in outings if same)
        switched = sum(1 for _, _, same in outings if not same)
        lines.append(f"{c_id}\t{potential}\t{same_boat}\t{switched}")
        total_potential += potential
        total_same_boat += same_boat
        total_switched += switched
    
    lines.append("")
    lines.append(f"TOTAL\t{total_potential}\t{total_same_boat}\t{total_switched}")
    lines.append("")
    lines.append("Detailed Double Outings")
    lines.append("Competitor\tFrom Race\tTo Race\tSame Boat?")
    
    for c_id in range(NUM_COMPETITORS):
        for r1, r2, same_boat in competitor_stats[c_id]:
            lines.append(f"{c_id}\t{r1}\t{r2}\t{'Yes' if same_boat else 'No'}")
    
    return "\n".join(lines)


def export_double_changeover_table(schedule: Schedule, filepath: str) -> None:
    """Export double changeover table to a TSV file."""
    tsv_content = double_changeover_table_to_tsv(schedule)
    with open(filepath, "w") as f:
        f.write(tsv_content)

