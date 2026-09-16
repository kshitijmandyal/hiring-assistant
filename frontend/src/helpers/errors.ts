/**
 * Turns RTK Query errors into something a user can act on.
 *
 * Messages are keyed by the backend's error code rather than its message text, which
 * is why the backend sends a stable code alongside the prose.
 */

import { isApiError } from '@/api/api';

const MESSAGES_BY_CODE: Record<string, string> = {
  VALIDATION_FAILED: 'Some details need correcting.',
  INVALID_EMAIL: 'That email address does not look right.',
  INVALID_PHONE: 'Include the country code, for example +91 98765 43210.',
  EMPTY_TECH_STACK: 'Add at least one technology.',
  TECH_STACK_TOO_LARGE: 'That is too many technologies — pick your strongest few.',
  DUPLICATE_CANDIDATE: 'Someone is already registered with that email.',
  CANDIDATE_NOT_FOUND: 'We could not find that candidate.',
  INTERVIEW_NOT_FOUND: 'We could not find that interview.',
  INTERVIEW_ALREADY_FINALISED: 'This interview is already complete.',
  INTERVIEW_NOT_READY: 'Answer at least one question before finishing.',
  LLM_RATE_LIMITED: 'We are being rate limited. Try again shortly.',
  LLM_UNAVAILABLE: 'The question service is unavailable right now.',
  QUESTION_GENERATION_FAILED: 'We could not generate questions. Please try again.',
  GRADING_FAILED: 'We could not grade the answers. Please try again.',
  STORAGE_FAILED: 'We could not save that. Please try again.',
};

const FALLBACK = 'Something went wrong. Please try again.';

export function getErrorMessage(error: unknown): string {
  if (!isApiError(error)) return FALLBACK;
  return MESSAGES_BY_CODE[error.data.code] ?? error.data.message ?? FALLBACK;
}

/** Shown alongside the message so a user can quote it when reporting a problem. */
export function getCorrelationId(error: unknown): string | null {
  return isApiError(error) ? error.data.correlation_id : null;
}

export function isRetryable(error: unknown): boolean {
  if (!isApiError(error)) return false;
  return ['LLM_RATE_LIMITED', 'LLM_UNAVAILABLE', 'QUESTION_GENERATION_FAILED', 'GRADING_FAILED']
    .includes(error.data.code);
}
