/**
 * Which candidate and interview the user is currently working through.
 *
 * Server data lives in the RTK Query cache; this slice holds only the pointers into
 * it, plus draft answers that have not been submitted yet. It is persisted like the
 * auth tokens, so a refresh mid-interview resumes instead of stranding a candidate
 * whose invite link has already been stripped from the URL.
 */

import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface SessionState {
  candidateId: string | null;
  interviewId: string | null;
  /** Keyed by question id. Kept out of the cache so typing does not invalidate it. */
  draftAnswers: Record<string, string>;
}

const STORAGE_KEY = 'talentscout.session';

const initialState: SessionState = {
  candidateId: null,
  interviewId: null,
  draftAnswers: {},
};

function readStored(): SessionState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return initialState;
    const parsed = JSON.parse(raw) as Partial<SessionState>;
    return {
      candidateId: parsed.candidateId ?? null,
      interviewId: parsed.interviewId ?? null,
      draftAnswers: parsed.draftAnswers ?? {},
    };
  } catch {
    // Private browsing, blocked storage, or a stale shape — start fresh.
    return initialState;
  }
}

function persist(state: SessionState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage unavailable; the session still works for this tab.
  }
}

const sessionSlice = createSlice({
  name: 'session',
  initialState: readStored(),
  reducers: {
    candidateStarted(state, action: PayloadAction<string>) {
      state.candidateId = action.payload;
      persist(state);
    },
    interviewStarted(state, action: PayloadAction<string>) {
      // Reopening the same invite link keeps the drafts typed so far.
      if (state.interviewId !== action.payload) state.draftAnswers = {};
      state.interviewId = action.payload;
      persist(state);
    },
    draftAnswerChanged(
      state,
      action: PayloadAction<{ questionId: string; text: string }>,
    ) {
      state.draftAnswers[action.payload.questionId] = action.payload.text;
      persist(state);
    },
    draftAnswerCleared(state, action: PayloadAction<string>) {
      delete state.draftAnswers[action.payload];
      persist(state);
    },
    sessionReset() {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {
        // Nothing stored to clear.
      }
      return initialState;
    },
  },
});

export const {
  candidateStarted,
  interviewStarted,
  draftAnswerChanged,
  draftAnswerCleared,
  sessionReset,
} = sessionSlice.actions;

export const sessionReducer = sessionSlice.reducer;
