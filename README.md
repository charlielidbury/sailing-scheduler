This repo defines a script which generates schedules for sailing competitions.

In the future the script will be made generic over the constants, but for now they're hardcoded to avoid having to come up with general algorithms.

# Competition Structure
- Each competition consists of a sequence of races.
- There are 2 sets of club boats, and the races alternate between using them. I.e. the first race will use the first set, then the second set, then the first set again, etc.
- Each race is 2 boats vs 2 boats. This pairing of boats forms a team.
- Which 2 competitors form a team is decided on a per-race basis, with the goal of maximising the number of unique teams in a schedule.
- There are 24 competitors in total.
- There are 48 races in total.

# Race Scheduling
A race schedule defines who is racing when. This consists of a list of races, each race takes roughly the following form:
race N:
    boat set: Cambridge set
    team A:
        competitor 1: Charlie
        competitor 2: Sam
    team B:
        competitor 1: John
        competitor 2: Jane

It is important to note that multiple races can run concurrently, since there are multiple sets of boats which can be raced at the same time, using different parts of the track by staggering the start times. The races might overlap like this:

| Boat Set A | Boat Set B |
|------------|------------|
| Race 1     |            |
| Race 1     |  Race 2    |
| Race 3     |  Race 2    |
| Race 3     |  Race 4    |
|            |  Race 4    |

## Schedule Requirements
1. Each competitor must be physically able to attend their races. With the current constants, this means they cannot attend adjacent races (since race N and race N+1 will be running at the same time).
2. Each competitor partakes in exactly 8 races.
3. Each competitor must not be scheduled to race with the same teammate more than once (i.e. all 8 of their races are with unique teammates)
4. two-race-per-outing: Ideally, each competitor gets in a boat, and completes **two races** in a row (due to the concurrent race situation, this means [race N, race N+2])
5. The two-race-per-outing preference likely can't be achieved perfectly, but it should be optimised such that single-race-outings are minimised.
6. The schedule must be interuptable: i.e. if it's cut short, every competitor should have raced approximately the same amount. This is best achieved by having the schedule take the form of a series of "rounds", where every competitor races twice in each round. (it's twice, not once, because of the two-race-per-outing preference)