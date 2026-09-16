/**
 * Routes by who is signed in and how far the screening has got.
 *
 * Two audiences share one app: an interviewer who signs in, and a candidate who
 * arrives on an invite link with a token scoped to a single interview.
 */

import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { AssessmentView } from '@/features/assessment/AssessmentView';
import { useGetAssessmentQuery } from '@/features/assessment/assessmentApi';
import { LoginForm } from '@/features/auth/LoginForm';
import { useLogoutMutation } from '@/features/auth/authApi';
import { CandidateForm } from '@/features/candidate/CandidateForm';
import { InterviewView } from '@/features/interview/InterviewView';
import { InviteLink } from '@/features/interview/InviteLink';
import { TechStackForm } from '@/features/interview/TechStackForm';
import { useInviteToken } from '@/hooks/useInviteToken';
import { loggedOut } from '@/store/authSlice';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { sessionReset } from '@/store/sessionSlice';
import type { Role } from '@/types/api';
import styles from './App.module.scss';

function InterviewerFlow() {
  const candidateId = useAppSelector((state) => state.session.candidateId);
  const interviewId = useAppSelector((state) => state.session.interviewId);

  // Once an assessment exists the interview is over, so results take precedence.
  const { data: assessment } = useGetAssessmentQuery(interviewId ?? '', {
    skip: !interviewId,
  });

  if (!candidateId) return <CandidateForm />;
  if (!interviewId) return <TechStackForm candidateId={candidateId} />;
  if (assessment) return <AssessmentView interviewId={interviewId} />;

  return (
    <Stack spacing={3}>
      <InviteLink interviewId={interviewId} />
      <InterviewView interviewId={interviewId} />
    </Stack>
  );
}

function CandidateFlow() {
  const interviewId = useAppSelector((state) => state.session.interviewId);

  if (!interviewId) {
    return (
      <Typography className="u-text-center u-text-muted">
        This invite link is missing its interview. Ask your interviewer for a new one.
      </Typography>
    );
  }
  return <InterviewView interviewId={interviewId} />;
}

function CurrentFlow({ role }: { role: Role | null }) {
  if (role === 'interviewer') return <InterviewerFlow />;
  if (role === 'candidate') return <CandidateFlow />;
  return <LoginForm />;
}

export default function App() {
  useInviteToken();

  const role = useAppSelector((state) => state.auth.role);
  const refreshToken = useAppSelector((state) => state.auth.refreshToken);
  const [logout] = useLogoutMutation();
  const dispatch = useAppDispatch();

  const handleSignOut = async () => {
    if (refreshToken) await logout(refreshToken).unwrap().catch(() => undefined);
    dispatch(loggedOut());
    dispatch(sessionReset());
  };

  return (
    <div className={styles.app}>
      <header className={styles.masthead}>
        <div className={`u-container ${styles.mastheadInner}`}>
          <Typography className={styles.brand}>TalentScout</Typography>
          {role === 'interviewer' && (
            <Button size="small" onClick={() => void handleSignOut()}>
              Sign out
            </Button>
          )}
        </div>
      </header>

      <main className="u-container">
        <CurrentFlow role={role} />
      </main>
    </div>
  );
}
