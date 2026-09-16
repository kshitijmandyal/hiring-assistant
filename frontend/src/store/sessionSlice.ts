/**
 * Which candidate and interview the user is currently working through.
 *
 * Server data lives in the RTK Query cache; this slice holds only the pointers into
 * it, plus draft answers that have not been submitted yet.
 */

import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface SessionState {
  candidateId: string | null;
  interviewId: string | null;
  /** Keyed by question id. Kept out of the cache so typing does not invalidate it. */
  draftAnswers: Record<string, string>;
}

const initialState: SessionState = {
  candidateId: null,
  interviewId: null,
  draftAnswers: {},
};

const sessionSlice = createSlice({
  name: 'session',
  initialState,
  reducers: {
    candidateStarted(state, action: PayloadAction<string>) {
      state.candidateId = action.payload;
    },
    interviewStarted(state, action: PayloadAction<string>) {
      state.interviewId = action.payload;
      state.draftAnswers = {};
    },
    draftAnswerChanged(
      state,
      action: PayloadAction<{ questionId: string; text: string }>,
    ) {
      state.draftAnswers[action.payload.questionId] = action.payload.text;
    },
    draftAnswerCleared(state, action: PayloadAction<string>) {
      delete state.draftAnswers[action.payload];
    },
    sessionReset() {
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
