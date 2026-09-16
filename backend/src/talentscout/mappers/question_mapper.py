"""LLM question schema -> domain Question."""

from talentscout.adapters.claude.schemas import LLMQuestion, LLMQuestionSet
from talentscout.domain.interview import Question


def to_domain_question(llm_question: LLMQuestion, *, technology: str) -> Question:
    return Question(
        technology=technology,
        prompt=llm_question.prompt,
        kind=llm_question.kind,
        rubric=llm_question.rubric,
    )


def to_domain_questions(question_set: LLMQuestionSet, *, technology: str) -> list[Question]:
    return [to_domain_question(q, technology=technology) for q in question_set.questions]
