/**
 * Derivations over interview data.
 *
 * Kept out of components so the render path stays declarative and these stay
 * independently readable.
 */

import type { Interview, Question, QuestionKind, Recommendation } from '@/types/api';

export interface TechnologyGroup {
  technology: string;
  questions: Question[];
}

/** Groups questions by technology, preserving the backend's ordering. */
export function groupQuestionsByTechnology(questions: Question[]): TechnologyGroup[] {
  const groups = new Map<string, Question[]>();
  for (const question of questions) {
    const existing = groups.get(question.technology);
    if (existing) {
      existing.push(question);
    } else {
      groups.set(question.technology, [question]);
    }
  }
  return [...groups].map(([technology, grouped]) => ({ technology, questions: grouped }));
}

export function getProgress(interview: Interview): {
  answered: number;
  total: number;
  percentage: number;
} {
  const total = interview.questions.length;
  const answered = interview.answered_question_ids.length;
  return {
    answered,
    total,
    percentage: total === 0 ? 0 : Math.round((answered / total) * 100),
  };
}

export function isAnswered(interview: Interview, questionId: string): boolean {
  return interview.answered_question_ids.includes(questionId);
}

const KIND_LABELS: Record<QuestionKind, string> = {
  conceptual: 'Concept',
  practical: 'Experience',
  debugging: 'Debugging',
  design: 'Design',
};

export function getKindLabel(kind: QuestionKind): string {
  return KIND_LABELS[kind];
}

const RECOMMENDATION_LABELS: Record<Recommendation, string> = {
  strong_proceed: 'Strong proceed',
  proceed: 'Proceed',
  borderline: 'Borderline',
  do_not_proceed: 'Do not proceed',
};

export function getRecommendationLabel(recommendation: Recommendation): string {
  return RECOMMENDATION_LABELS[recommendation];
}

export function formatSeniority(seniority: string): string {
  return seniority.charAt(0).toUpperCase() + seniority.slice(1);
}
