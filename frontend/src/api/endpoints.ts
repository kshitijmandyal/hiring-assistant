/**
 * Every API path in one place. Nothing else in the app builds a URL by hand, so a
 * backend route change is a one-file edit.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const ENDPOINTS = {
  candidates: {
    create: () => '/candidates',
    byId: (candidateId: string) => `/candidates/${candidateId}`,
    interviews: (candidateId: string) => `/candidates/${candidateId}/interviews`,
  },
  interviews: {
    byId: (interviewId: string) => `/interviews/${interviewId}`,
    answers: (interviewId: string) => `/interviews/${interviewId}/answers`,
    assessment: (interviewId: string) => `/interviews/${interviewId}/assessment`,
  },
} as const;

export const CORRELATION_ID_HEADER = 'X-Correlation-ID';
