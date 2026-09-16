/**
 * Auth state.
 *
 * Tokens live in localStorage so a refresh does not log the interviewer out. That
 * trades some XSS exposure for usability, which is the right call here: the access
 * token lasts 15 minutes and the app renders no user-supplied HTML.
 */

import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

import type { Role } from '@/types/api';

const STORAGE_KEY = 'talentscout.auth';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  role: Role | null;
}

interface StoredTokens {
  accessToken: string;
  refreshToken: string | null;
  role: Role;
}

function readStored(): AuthState {
  const empty: AuthState = { accessToken: null, refreshToken: null, role: null };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return empty;
    const parsed = JSON.parse(raw) as StoredTokens;
    return {
      accessToken: parsed.accessToken ?? null,
      refreshToken: parsed.refreshToken ?? null,
      role: parsed.role ?? null,
    };
  } catch {
    // Private browsing, blocked storage, or a stale shape — start logged out.
    return empty;
  }
}

function persist(state: AuthState): void {
  try {
    if (!state.accessToken) {
      localStorage.removeItem(STORAGE_KEY);
      return;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage unavailable; the session still works for this tab.
  }
}

const authSlice = createSlice({
  name: 'auth',
  initialState: readStored(),
  reducers: {
    credentialsReceived(
      state,
      action: PayloadAction<{ accessToken: string; refreshToken: string; role: Role }>,
    ) {
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.role = action.payload.role;
      persist(state);
    },
    /** A candidate arriving via an invite link: one token, nothing to refresh. */
    inviteAccepted(state, action: PayloadAction<string>) {
      state.accessToken = action.payload;
      state.refreshToken = null;
      state.role = 'candidate';
      persist(state);
    },
    loggedOut(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.role = null;
      persist(state);
    },
  },
});

export const { credentialsReceived, inviteAccepted, loggedOut } = authSlice.actions;
export const authReducer = authSlice.reducer;
