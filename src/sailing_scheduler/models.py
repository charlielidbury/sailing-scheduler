"""Data models for the sailing scheduler."""

from dataclasses import dataclass
from enum import Enum


class BoatSet(Enum):
    """The two sets of club boats that alternate between races."""
    A = "A"
    B = "B"


@dataclass(frozen=True)
class Competitor:
    """A competitor in the sailing competition."""
    id: int
    name: str

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Competitor):
            return NotImplemented
        return self.id == other.id


@dataclass(frozen=True)
class Team:
    """
    A team of 2 competitors racing together.
    
    The order matters for boat positions:
    - competitor1 is in the first boat position (7 for team_a, 10 for team_b)
    - competitor2 is in the second boat position (8 for team_a, 11 for team_b)
    """
    competitor1: Competitor
    competitor2: Competitor

    # NOTE: No auto-reordering - order matters for boat positions!

    @property
    def competitors(self) -> frozenset[Competitor]:
        return frozenset({self.competitor1, self.competitor2})

    def __hash__(self) -> int:
        return hash(self.competitors)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return NotImplemented
        return self.competitors == other.competitors


@dataclass
class Race:
    """A single race between two teams."""
    race_number: int
    boat_set: BoatSet
    team_a: Team
    team_b: Team

    @property
    def all_competitors(self) -> frozenset[Competitor]:
        return self.team_a.competitors | self.team_b.competitors


@dataclass
class Schedule:
    """A complete race schedule."""
    races: list[Race]
    competitors: list[Competitor]

    def get_races_for_competitor(self, competitor: Competitor) -> list[Race]:
        """Get all races that a specific competitor participates in."""
        return [
            race for race in self.races
            if competitor in race.all_competitors
        ]

    def get_race_numbers_for_competitor(self, competitor: Competitor) -> list[int]:
        """Get all race numbers for a specific competitor, sorted."""
        return sorted(race.race_number for race in self.get_races_for_competitor(competitor))

    def get_teammates_for_competitor(self, competitor: Competitor) -> list[Competitor]:
        """Get all unique teammates for a competitor across all their races."""
        teammates = []
        for race in self.get_races_for_competitor(competitor):
            for team in [race.team_a, race.team_b]:
                if competitor in team.competitors:
                    for c in team.competitors:
                        if c != competitor:
                            teammates.append(c)
        return teammates


# Constants for the current competition
NUM_COMPETITORS = 25
NUM_RACES = 96
RACES_PER_COMPETITOR = 16  # Target for those who never sit out
MIN_RACES_PER_COMPETITOR = 14  # For those who sit out once
COMPETITORS_PER_ROUND = 24  # Chain structure needs exactly 24

