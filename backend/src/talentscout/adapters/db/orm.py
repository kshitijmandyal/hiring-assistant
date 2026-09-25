"""SQLAlchemy table definitions.

Deliberately separate from the domain models: the domain is frozen and behaviour-rich,
these are mutable row objects. Mappers translate between them, so a schema change never
forces a domain change.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CandidateRow(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    # Normalised to lowercase in the domain, so a plain unique index is enough
    # to stop the same person registering twice.
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20))
    years_of_experience: Mapped[float] = mapped_column(Float)
    desired_positions: Mapped[list[str]] = mapped_column(JSONB)
    location: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    interviews: Mapped[list["InterviewRow"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class InterviewRow(Base):
    __tablename__ = "interviews"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    seniority: Mapped[str] = mapped_column(String(20))
    tech_stack: Mapped[list[str]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finalised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidate: Mapped[CandidateRow] = relationship(back_populates="interviews")
    questions: Mapped[list["QuestionRow"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="QuestionRow.position",
    )


class QuestionRow(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    interview_id: Mapped[UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), index=True
    )
    # Generation order is the presentation order; without it, questions for one
    # technology would be interleaved arbitrarily on reload.
    position: Mapped[int] = mapped_column(Integer)
    technology: Mapped[str] = mapped_column(String(40))
    prompt: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))
    rubric: Mapped[list[str]] = mapped_column(JSONB)

    interview: Mapped[InterviewRow] = relationship(back_populates="questions")
    answer: Mapped["AnswerRow | None"] = relationship(
        back_populates="question", cascade="all, delete-orphan", uselist=False
    )


class AnswerRow(Base):
    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("question_id", name="uq_answers_question_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    question: Mapped[QuestionRow] = relationship(back_populates="answer")


class AssessmentRow(Base):
    __tablename__ = "assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # One assessment per interview. The previous implementation appended a duplicate
    # record every time the candidate pressed finalise.
    interview_id: Mapped[UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, index=True
    )
    questions_total: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(String(20))
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    question_assessments: Mapped[list["QuestionAssessmentRow"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class QuestionAssessmentRow(Base):
    __tablename__ = "question_assessments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer)
    strengths: Mapped[list[str]] = mapped_column(JSONB, default=list)
    gaps: Mapped[list[str]] = mapped_column(JSONB, default=list)
    guardrail_flags: Mapped[list[str]] = mapped_column(JSONB, default=list)

    assessment: Mapped[AssessmentRow] = relationship(back_populates="question_assessments")
    criterion_scores: Mapped[list["CriterionScoreRow"]] = relationship(
        back_populates="question_assessment", cascade="all, delete-orphan"
    )


class CriterionScoreRow(Base):
    __tablename__ = "criterion_scores"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    question_assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_assessments.id", ondelete="CASCADE"), index=True
    )
    criterion: Mapped[str] = mapped_column(Text)
    met: Mapped[bool] = mapped_column(Boolean)
    justification: Mapped[str] = mapped_column(Text)

    question_assessment: Mapped[QuestionAssessmentRow] = relationship(
        back_populates="criterion_scores"
    )


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    refresh_tokens: Mapped[list["RefreshTokenRow"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshTokenRow(Base):
    """One row per issued refresh token, so a session can actually be revoked.

    Only the jti is stored — the token itself is never persisted, so a database leak
    does not hand over usable sessions.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    jti: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[UserRow] = relationship(back_populates="refresh_tokens")


class AuthAttemptRow(Base):
    """One row per counted login or registration attempt, for brute-force limits.

    The key is a SHA-256 of the email or IP, so the table holds no raw PII. Rows past
    their window are deleted as new ones arrive, which keeps it small.
    """

    __tablename__ = "auth_attempts"
    __table_args__ = (Index("ix_auth_attempts_kind_key_created_at", "kind", "key", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    key: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
