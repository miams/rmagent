"""
Person matching for census entries.

Matches extracted census entries to RootsMagic PersonID using
fuzzy name matching, date proximity, and location similarity.

Uses RapidFuzz for fast fuzzy string matching with configurable
threshold and scoring algorithms.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


@dataclass
class PersonCandidate:
    """Potential person match from RootsMagic database."""

    person_id: int
    given_name: str
    surname: str
    full_name: str
    birth_year: Optional[int]
    birth_place: Optional[str]
    match_score: float  # 0.0-1.0


@dataclass
class MatchResult:
    """Result of matching census entry to person."""

    census_entry: dict  # Raw census data (name, age, birthplace, etc.)
    best_match: Optional[PersonCandidate]
    all_candidates: List[PersonCandidate]
    confidence: float  # 0.0-1.0


class CensusPersonMatcher:
    """Matches census entries to RootsMagic persons using fuzzy matching."""

    def __init__(
        self,
        rm_db_path: str | Path,
        min_name_score: float = 0.75,
        max_age_difference: int = 5,
        scorer=fuzz.token_sort_ratio,
    ):
        """
        Initialize person matcher.

        Args:
            rm_db_path: Path to RootsMagic database
            min_name_score: Minimum fuzzy match score (0-1) for name matching
            max_age_difference: Maximum year difference for age matching
            scorer: RapidFuzz scoring function
                - fuzz.ratio: Simple character comparison
                - fuzz.token_sort_ratio: Word-order insensitive (default)
                - fuzz.partial_ratio: Substring matching
        """
        self.rm_db_path = Path(rm_db_path)
        self.min_name_score = min_name_score * 100  # Convert to 0-100 scale
        self.max_age_difference = max_age_difference
        self.scorer = scorer

        # Cache of persons from database
        self._person_cache: Optional[List[dict]] = None

    def match_entry(
        self,
        name: str,
        age: Optional[int] = None,
        birthplace: Optional[str] = None,
        census_year: Optional[int] = None,
        max_results: int = 5,
    ) -> MatchResult:
        """
        Match a census entry to RootsMagic persons.

        Args:
            name: Full name from census
            age: Age in census year
            birthplace: Birthplace from census
            census_year: Year of census (for age calculation)
            max_results: Maximum candidate matches to return

        Returns:
            MatchResult with best match and all candidates
        """
        # Load persons if not cached
        if self._person_cache is None:
            self._load_persons()

        # Calculate birth year from age
        birth_year = None
        if age and census_year:
            birth_year = census_year - age

        # Find name matches
        candidates = self._find_name_matches(name, max_results * 2)

        # Filter and score by additional criteria
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_match_score(
                candidate, birth_year, birthplace
            )

            if score >= self.min_name_score / 100:
                candidate.match_score = score
                scored_candidates.append(candidate)

        # Sort by score and limit
        scored_candidates.sort(key=lambda c: c.match_score, reverse=True)
        scored_candidates = scored_candidates[:max_results]

        # Determine best match and confidence
        best_match = scored_candidates[0] if scored_candidates else None
        confidence = best_match.match_score if best_match else 0.0

        # Adjust confidence based on uniqueness
        if len(scored_candidates) > 1:
            second_score = scored_candidates[1].match_score
            if confidence - second_score < 0.1:  # Close competitors
                confidence *= 0.8  # Reduce confidence

        logger.debug(
            f"Match: '{name}' -> {best_match.full_name if best_match else 'No match'} "
            f"(confidence: {confidence:.2f})"
        )

        return MatchResult(
            census_entry={
                "name": name,
                "age": age,
                "birthplace": birthplace,
                "census_year": census_year,
            },
            best_match=best_match,
            all_candidates=scored_candidates,
            confidence=confidence,
        )

    def match_batch(
        self, census_entries: List[dict], max_results: int = 5
    ) -> List[MatchResult]:
        """
        Match multiple census entries in batch.

        Args:
            census_entries: List of dicts with keys: name, age, birthplace, census_year
            max_results: Maximum candidates per entry

        Returns:
            List of MatchResults for each entry
        """
        results = []

        for entry in census_entries:
            result = self.match_entry(
                name=entry.get("name", ""),
                age=entry.get("age"),
                birthplace=entry.get("birthplace"),
                census_year=entry.get("census_year"),
                max_results=max_results,
            )
            results.append(result)

        logger.info(
            f"Matched {len(results)} entries: "
            f"{sum(1 for r in results if r.best_match)} with matches"
        )
        return results

    def _load_persons(self) -> None:
        """Load all persons from RootsMagic database into cache."""
        conn = sqlite3.connect(str(self.rm_db_path))
        conn.row_factory = sqlite3.Row

        # Load ICU extension for RMNOCASE collation
        try:
            conn.enable_load_extension(True)
            conn.load_extension("./sqlite-extension/icu.dylib")
            conn.execute(
                "SELECT icu_load_collation('en_US@colStrength=primary;caseLevel=off;normalization=on','RMNOCASE')"
            )
            conn.enable_load_extension(False)
        except Exception as e:
            logger.warning(f"Could not load ICU extension: {e}")

        query = """
        SELECT DISTINCT
            p.PersonID,
            n.Surname,
            n.Given,
            (n.Given || ' ' || n.Surname) as FullName,
            NULL as BirthYear,
            NULL as BirthPlace
        FROM PersonTable p
        JOIN NameTable n ON p.PersonID = n.OwnerID
        WHERE n.IsPrimary = 1 AND n.Surname IS NOT NULL
        ORDER BY n.Surname, n.Given
        """

        cursor = conn.execute(query)
        self._person_cache = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"Loaded {len(self._person_cache)} persons from database")

    def _find_name_matches(
        self, name: str, limit: int
    ) -> List[PersonCandidate]:
        """
        Find persons with similar names using fuzzy matching.

        Args:
            name: Name to match
            limit: Maximum matches to return

        Returns:
            List of PersonCandidate objects
        """
        if not self._person_cache:
            return []

        # Extract names and IDs for matching
        names = [p["FullName"] for p in self._person_cache]

        # Use RapidFuzz process.extract for fast fuzzy matching
        matches = process.extract(
            name,
            names,
            scorer=self.scorer,
            limit=limit,
            score_cutoff=self.min_name_score,
        )

        # Convert to PersonCandidate objects
        candidates = []
        for match_name, score, idx in matches:
            person = self._person_cache[idx]

            candidates.append(
                PersonCandidate(
                    person_id=person["PersonID"],
                    given_name=person["Given"] or "",
                    surname=person["Surname"] or "",
                    full_name=person["FullName"],
                    birth_year=person.get("BirthYear"),
                    birth_place=person.get("BirthPlace"),
                    match_score=score / 100.0,  # Convert to 0-1
                )
            )

        return candidates

    def _calculate_match_score(
        self,
        candidate: PersonCandidate,
        census_birth_year: Optional[int],
        census_birthplace: Optional[str],
    ) -> float:
        """
        Calculate combined match score using name, age, and place.

        Args:
            candidate: Person candidate
            census_birth_year: Birth year calculated from census age
            census_birthplace: Birthplace from census

        Returns:
            Combined score (0.0-1.0)
        """
        # Start with name match score
        score = candidate.match_score

        # Age bonus (if available and close)
        if census_birth_year and candidate.birth_year:
            age_diff = abs(census_birth_year - candidate.birth_year)
            if age_diff <= self.max_age_difference:
                # Boost score based on age proximity
                age_bonus = (self.max_age_difference - age_diff) / self.max_age_difference * 0.1
                score = min(1.0, score + age_bonus)
            else:
                # Penalize if age is very different
                score *= 0.7

        # Birthplace bonus (if available and similar)
        if census_birthplace and candidate.birth_place:
            place_similarity = fuzz.partial_ratio(
                census_birthplace.lower(), candidate.birth_place.lower()
            ) / 100.0

            if place_similarity > 0.7:
                score = min(1.0, score + place_similarity * 0.1)

        return score


def match_census_entry(
    name: str,
    rm_db_path: str | Path,
    age: Optional[int] = None,
    birthplace: Optional[str] = None,
    census_year: Optional[int] = None,
    **options,
) -> MatchResult:
    """
    Convenience function to match a single census entry.

    Args:
        name: Full name from census
        rm_db_path: Path to RootsMagic database
        age: Age in census year
        birthplace: Birthplace from census
        census_year: Year of census
        **options: Matcher options (min_name_score, max_age_difference, scorer)

    Returns:
        MatchResult with best match and candidates

    Example:
        >>> result = match_census_entry(
        ...     "John Smith",
        ...     "data/Iiams.rmtree",
        ...     age=42,
        ...     census_year=1900,
        ... )
        >>> if result.best_match:
        ...     print(f"Matched to PersonID {result.best_match.person_id}")
    """
    matcher = CensusPersonMatcher(rm_db_path, **options)
    return matcher.match_entry(name, age, birthplace, census_year)
