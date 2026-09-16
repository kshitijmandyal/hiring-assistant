"""Interview ORM rows <-> domain aggregate."""

from uuid import UUID, uuid4

from talentscout.adapters.db.orm import AnswerRow, InterviewRow, QuestionRow
from talentscout.domain.enums import InterviewStatus, QuestionKind, SeniorityLevel
from talentscout.domain.interview import Answer, Interview, Question


def to_interview_row(interview: Interview) -> InterviewRow:
    """The interview row alone; questions and answers are synced separately because
    saving is an upsert over an existing aggregate rather than a fresh insert.
    """
    return InterviewRow(
        id=interview.id,
        candidate_id=interview.candidate_id,
        seniority=interview.seniority.value,
        tech_stack=list(interview.tech_stack),
        status=interview.status.value,
        created_at=interview.created_at,
        finalised_at=interview.finalised_at,
    )


def to_question_row(question: Question, *, interview_id: UUID, position: int) -> QuestionRow:
    return QuestionRow(
        id=question.id,
        interview_id=interview_id,
        position=position,
        technology=question.technology,
        prompt=question.prompt,
        kind=question.kind.value,
        rubric=list(question.rubric),
    )


def to_answer_row(answer: Answer) -> AnswerRow:
    return AnswerRow(
        id=uuid4(),
        question_id=answer.question_id,
        text=answer.text,
        submitted_at=answer.submitted_at,
    )


def to_domain_question(row: QuestionRow) -> Question:
    return Question(
        id=row.id,
        technology=row.technology,
        prompt=row.prompt,
        kind=QuestionKind(row.kind),
        rubric=list(row.rubric),
    )


def to_domain_answer(row: AnswerRow) -> Answer:
    return Answer(
        question_id=row.question_id,
        text=row.text,
        submitted_at=row.submitted_at,
    )


def to_domain(row: InterviewRow) -> Interview:
    answers = {
        question.answer.question_id: to_domain_answer(question.answer)
        for question in row.questions
        if question.answer is not None
    }
    return Interview(
        id=row.id,
        candidate_id=row.candidate_id,
        seniority=SeniorityLevel(row.seniority),
        tech_stack=list(row.tech_stack),
        questions=[to_domain_question(q) for q in row.questions],
        answers=answers,
        status=InterviewStatus(row.status),
        created_at=row.created_at,
        finalised_at=row.finalised_at,
    )
