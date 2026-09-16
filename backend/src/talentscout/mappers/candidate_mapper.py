"""Candidate ORM row <-> domain model."""

from talentscout.adapters.db.orm import CandidateRow
from talentscout.domain.candidate import Candidate


def to_row(candidate: Candidate) -> CandidateRow:
    return CandidateRow(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        years_of_experience=candidate.years_of_experience,
        desired_positions=list(candidate.desired_positions),
        location=candidate.location,
        created_at=candidate.created_at,
    )


def to_domain(row: CandidateRow) -> Candidate:
    return Candidate(
        id=row.id,
        full_name=row.full_name,
        email=row.email,
        phone=row.phone,
        years_of_experience=row.years_of_experience,
        desired_positions=list(row.desired_positions),
        location=row.location,
        created_at=row.created_at,
    )
