"""Census person matching pipeline."""

from rmagent.census.pipelines.matching.person_matcher import (
    CensusPersonMatcher,
    MatchResult,
    PersonCandidate,
    match_census_entry,
)

__all__ = [
    "CensusPersonMatcher",
    "MatchResult",
    "PersonCandidate",
    "match_census_entry",
]
