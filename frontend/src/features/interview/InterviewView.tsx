import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { ErrorNotice } from '@/components/ErrorNotice';
import { LoadingState } from '@/components/LoadingState';
import { useFinaliseInterviewMutation } from '@/features/assessment/assessmentApi';
import { getProgress, groupQuestionsByTechnology, isAnswered } from '@/helpers/interview';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { draftAnswerChanged } from '@/store/sessionSlice';
import { QuestionCard } from './QuestionCard';
import { useGetInterviewQuery, useSubmitAnswerMutation } from './interviewApi';
import styles from './InterviewView.module.scss';

interface InterviewViewProps {
  interviewId: string;
}

export function InterviewView({ interviewId }: InterviewViewProps) {
  const { data: interview, isLoading, error, refetch } = useGetInterviewQuery(interviewId);
  const [submitAnswer, { isLoading: submitting, error: submitError }] =
    useSubmitAnswerMutation();
  const [finalise, { isLoading: finalising, error: finaliseError }] =
    useFinaliseInterviewMutation();

  const drafts = useAppSelector((state) => state.session.draftAnswers);
  const dispatch = useAppDispatch();

  if (isLoading) return <LoadingState message="Loading your interview…" />;
  if (error != null) return <ErrorNotice error={error} onRetry={refetch} />;
  if (!interview) return null;

  const progress = getProgress(interview);
  const groups = groupQuestionsByTechnology(interview.questions);

  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <Stack spacing={1}>
          <Typography variant="h5" component="h1">
            Your questions
          </Typography>
          <Typography className="u-text-muted">
            {interview.tech_stack.join(' · ')}
          </Typography>
        </Stack>

        <Stack spacing={0.5}>
          <Typography className="u-text-sm">
            {progress.answered} of {progress.total} answered
          </Typography>
          <LinearProgress
            variant="determinate"
            value={progress.percentage}
            aria-label="Interview progress"
          />
        </Stack>
      </header>

      {submitError != null && <ErrorNotice error={submitError} />}

      {groups.map((group) => (
        <section key={group.technology} className={styles.group}>
          <Typography variant="h6" component="h2" className={styles.technology}>
            {group.technology}
          </Typography>
          <Stack spacing={2}>
            {group.questions.map((question) => {
              const globalIndex = interview.questions.findIndex((q) => q.id === question.id);
              return (
                <QuestionCard
                  key={question.id}
                  question={question}
                  index={globalIndex}
                  draft={drafts[question.id] ?? ''}
                  answered={isAnswered(interview, question.id)}
                  submitting={submitting}
                  onDraftChange={(text) =>
                    dispatch(draftAnswerChanged({ questionId: question.id, text }))
                  }
                  onSubmit={() =>
                    void submitAnswer({
                      interviewId,
                      body: {
                        question_id: question.id,
                        text: (drafts[question.id] ?? '').trim(),
                      },
                    })
                  }
                />
              );
            })}
          </Stack>
        </section>
      ))}

      {finaliseError != null && <ErrorNotice error={finaliseError} />}

      <footer className={styles.footer}>
        <Typography className="u-text-sm u-text-muted">
          {progress.answered === 0
            ? 'Answer at least one question to finish.'
            : progress.answered < progress.total
              ? `${progress.total - progress.answered} unanswered. You can finish anyway — coverage is reported separately from your score.`
              : 'All questions answered.'}
        </Typography>
        <Button
          variant="contained"
          size="large"
          disabled={progress.answered === 0 || finalising}
          onClick={() => void finalise(interviewId)}
        >
          {finalising ? 'Grading…' : 'Finish and get results'}
        </Button>
      </footer>
    </div>
  );
}
