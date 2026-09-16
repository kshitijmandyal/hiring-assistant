/**
 * Centralised API configuration.
 *
 * Owns the base query and error normalisation; feature slices inject their endpoints
 * into this one API object so there is a single cache and a single place to change
 * transport concerns.
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { FetchBaseQueryError } from '@reduxjs/toolkit/query/react';

import { API_BASE_URL } from './endpoints';
import type { ApiError } from '@/types/api';

export const TAG_TYPES = ['Candidate', 'Interview', 'Assessment'] as const;

const baseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  prepareHeaders: (headers) => {
    headers.set('Content-Type', 'application/json');
    return headers;
  },
});

export const api = createApi({
  reducerPath: 'api',
  baseQuery,
  tagTypes: TAG_TYPES,
  // Assessments can take a while to generate; refetching on focus mid-interview
  // would be both wasteful and confusing.
  refetchOnFocus: false,
  refetchOnReconnect: true,
  endpoints: () => ({}),
});

/** Narrows an RTK Query error to the backend's error body, when it is one. */
export function isApiError(error: unknown): error is FetchBaseQueryError & { data: ApiError } {
  if (typeof error !== 'object' || error === null || !('status' in error)) return false;
  const data = (error as FetchBaseQueryError).data;
  return typeof data === 'object' && data !== null && 'code' in data && 'message' in data;
}
