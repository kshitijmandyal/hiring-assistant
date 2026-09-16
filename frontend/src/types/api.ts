/**
 * Mirrors the backend's response schemas. Generated equivalents can replace this
 * from /openapi.json later; until then it is the single definition of the contract.
 */

export type Role = 'interviewer' | 'candidate';

export type Seniority = 'junior' | 'intermediate' | 'senior' | 'principal';

export type QuestionKind = 'conceptual' | 'practical' | 'debugging' | 'design';

export type InterviewStatus = 'draft' | 'questions_ready' | 'in_progress' | 'finalised';

export type Recommendation =
  | 'strong_proceed'
  | 'proceed'
  | 'borderline'
  | 'do_not_proceed';

export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  years_of_experience: number;
  desired_positions: string[];
  location: string;
  seniority: Seniority;
  created_at: string;
}

export interface CandidateCreateRequest {
  full_name: string;
  email: string;
  phone: string;
  years_of_experience: number;
  desired_positions: string[];
  location: string;
}

/** The rubric is intentionally absent — the backend withholds it from candidates. */
export interface Question {
  id: string;
  technology: string;
  prompt: string;
  kind: QuestionKind;
}

export interface Interview {
  id: string;
  candidate_id: string;
  seniority: Seniority;
  tech_stack: string[];
  status: InterviewStatus;
  questions: Question[];
  answered_question_ids: string[];
  created_at: string;
  finalised_at: string | null;
}

export interface InterviewStartRequest {
  tech_stack: string[];
  questions_per_technology?: number;
}

export interface AnswerSubmitRequest {
  question_id: string;
  text: string;
}

export interface CriterionScore {
  criterion: string;
  met: boolean;
  justification: string;
}

export interface QuestionAssessment {
  question_id: string;
  score: number;
  criterion_scores: CriterionScore[];
  strengths: string[];
  gaps: string[];
  /** Non-empty when a guardrail adjusted this grade; worth a manual read. */
  guardrail_flags: string[];
}

export interface Assessment {
  interview_id: string;
  question_assessments: QuestionAssessment[];
  questions_answered: number;
  questions_total: number;
  coverage: number;
  average_score: number;
  score_percentage: number;
  summary: string;
  recommendation: Recommendation;
  assessed_at: string;
}

/** Uniform error body. Branch on `code`, never on `message`. */
export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
  correlation_id: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface Invite {
  interview_id: string;
  invite_token: string;
  expires_in_days: number;
}
