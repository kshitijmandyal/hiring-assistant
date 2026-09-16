import { useEffect } from 'react';

import { useAppDispatch } from '@/store/hooks';
import { inviteAccepted } from '@/store/authSlice';
import { interviewStarted } from '@/store/sessionSlice';

const INVITE_PARAM = 'invite';

/**
 * Accepts a candidate's invite token from the URL, then strips it.
 *
 * Removing it from the address bar keeps the credential out of screenshots, browser
 * history, and any Referer header the page later sends.
 */
export function useInviteToken(): void {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get(INVITE_PARAM);
    if (!token) return;

    dispatch(inviteAccepted(token));

    // The token states which interview it opens. Reading the claim saves a lookup;
    // it is not trusted for access control, which the backend enforces from the
    // signature on every request.
    const interviewId = readInterviewId(token);
    if (interviewId) dispatch(interviewStarted(interviewId));

    params.delete(INVITE_PARAM);
    const query = params.toString();
    window.history.replaceState(
      {},
      '',
      window.location.pathname + (query ? `?${query}` : ''),
    );
  }, [dispatch]);
}

function readInterviewId(token: string): string | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    const claims = JSON.parse(json) as { interview_id?: string };
    return claims.interview_id ?? null;
  } catch {
    return null;
  }
}
