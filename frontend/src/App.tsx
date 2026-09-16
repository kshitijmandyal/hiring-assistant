/**
 * Routes the candidate through the screening by session state.
 *
 * The flow is linear (details -> tech stack -> questions -> results), so which step
 * to show is derived from what exists rather than stored as a separate step counter.
 */

import Typography from '@mui/material/Typography';

import { AssessmentView } from '@/features/assessment/AssessmentView';
import { useGetAssessmentQuery } from '@/features/assessment/assessmentApi';
import { CandidateForm } from '@/features/candidate/CandidateForm';
import { InterviewView } from '@/features/interview/InterviewView';
import { TechStackForm } from '@/features/interview/TechStackForm';
import { useAppSelector } from '@/store/hooks';
import styles from './App.module.scss';

function ScreeningFlow() {
  const candidateId = useAppSelector((state) => state.session.candidateId);
  const interviewId = useAppSelector((state) => state.session.interviewId);

  // Once an assessment exists the interview is over, so results take precedence.
  const { data: assessment } = useGetAssessmentQuery(interviewId ?? '', {
    skip: !interviewId,
  });

  if (!candidateId) return <CandidateForm />;
  if (!interviewId) return <TechStackForm candidateId={candidateId} />;
  if (assessment) return <AssessmentView interviewId={interviewId} />;
  return <InterviewView interviewId={interviewId} />;
}

export default function App() {
  return (
    <div className={styles.app}>
      <header className={styles.masthead}>
        <div className="u-container">
          <Typography className={styles.brand}>TalentScout</Typography>
        </div>
      </header>

      <main className="u-container">
        <ScreeningFlow />
      </main>
    </div>
  );
}
