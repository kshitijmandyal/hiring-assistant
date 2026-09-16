/**
 * Centralised API configuration.
 *
 * Owns the base query, bearer-token injection, and the refresh-on-401 retry. Feature
 * slices inject their endpoints into this one API object, so there is a single cache
 * and a single place to change transport concerns.
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  BaseQueryFn,
  FetchArgs,
  FetchBaseQueryError,
} from '@reduxjs/toolkit/query/react';
import { Mutex } from 'async-mutex';

import { API_BASE_URL, ENDPOINTS } from './endpoints';
import { credentialsReceived, loggedOut } from '@/store/authSlice';
import type { ApiError, Role } from '@/types/api';

export const TAG_TYPES = ['Candidate', 'Interview', 'Assessment', 'User'] as const;

// Serialises refresh attempts: without it, several 401s at once would each fire a
// refresh, and rotation would invalidate the token the others are still using.
const refreshMutex = new Mutex();

const rawBaseQuery = fetchBaseQuery({
  baseUrl: API_BASE_URL,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as { auth: { accessToken: string | null } }).auth.accessToken;
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return headers;
  },
});

const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  await refreshMutex.waitForUnlock();
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error?.status !== 401) return result;

  const state = api.getState() as { auth: { refreshToken: string | null } };
  // Candidates hold an invite token with nothing to refresh; a 401 there is final.
  if (!state.auth.refreshToken) {
    api.dispatch(loggedOut());
    return result;
  }

  if (refreshMutex.isLocked()) {
    await refreshMutex.waitForUnlock();
    return rawBaseQuery(args, api, extraOptions);
  }

  const release = await refreshMutex.acquire();
  try {
    const refreshResult = await rawBaseQuery(
      {
        url: ENDPOINTS.auth.refresh(),
        method: 'POST',
        body: { refresh_token: state.auth.refreshToken },
      },
      api,
      extraOptions,
    );

    const data = refreshResult.data as
      | { access_token: string; refresh_token: string }
      | undefined;

    if (!data) {
      api.dispatch(loggedOut());
      return result;
    }

    api.dispatch(
      credentialsReceived({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        role: 'interviewer' as Role,
      }),
    );
    result = await rawBaseQuery(args, api, extraOptions);
  } finally {
    release();
  }

  return result;
};

export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: TAG_TYPES,
  // Assessments take a while to generate; refetching on focus mid-interview would be
  // both wasteful and confusing.
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
