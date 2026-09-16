import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CancelIcon from '@mui/icons-material/Cancel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { ErrorNotice } from '@/components/ErrorNotice';
import { LoadingState } from '@/components/LoadingState';
import { useGetInterviewQuery } from '@/features/interview/interviewApi';
import { getRecommendationLabel } from '@/helpers/interview';
import { useGetAssessmentQuery } from './assessmentApi';
import styles from './AssessmentView.module.scss';

interface AssessmentViewProps {
  interviewId: string;
}

export function AssessmentView({ interviewId }: AssessmentViewProps) {
  const { data: assessment, isLoading, error, refetch } = useGetAssessmentQuery(interviewId);
  const { data: interview } = useGetInterviewQuery(interviewId);

  if (isLoading) return <LoadingState message="Loading your results…" />;
  if (error != null) return <ErrorNotice error={error} onRetry={refetch} />;
  if (!assessment) return null;

  const questionsById = new Map(interview?.questions.map((q) => [q.id, q]) ?? []);
  const flagged = assessment.question_assessments.filter(
    (qa) => qa.guardrail_flags.length > 0,
  );

  return (
    <div className={styles.view}>
      <header className={styles.summary}>
        <Stack spacing={1}>
          <Typography variant="h5" component="h1">
            Results
          </Typography>
          <Chip
            label={getRecommendationLabel(assessment.recommendation)}
            className={styles[assessment.recommendation] ?? ''}
          />
        </Stack>

        <Typography>{assessment.summary}</Typography>

        <div className={styles.metrics}>
          <div className={styles.metric}>
            <Typography className={styles.metricValue}>
              {assessment.score_percentage}%
            </Typography>
            <Typography className="u-text-sm u-text-muted">
              Average across answered
            </Typography>
          </div>
          <div className={styles.metric}>
            <Typography className={styles.metricValue}>
              {assessment.questions_answered}/{assessment.questions_total}
            </Typography>
            <Typography className="u-text-sm u-text-muted">Questions answered</Typography>
          </div>
        </div>

        <Stack spacing={0.5}>
          <Typography className="u-text-xs u-text-muted">
            Coverage {Math.round(assessment.coverage * 100)}% — reported separately from
            score, so unanswered questions do not count as wrong answers.
          </Typography>
          <LinearProgress
            variant="determinate"
            value={assessment.coverage * 100}
            aria-label="Question coverage"
          />
        </Stack>
      </header>

      {flagged.length > 0 && (
        <Alert severity="warning">
          {flagged.length} {flagged.length === 1 ? 'answer was' : 'answers were'} adjusted by
          an automated check. Read {flagged.length === 1 ? 'it' : 'them'} manually before
          relying on the score.
        </Alert>
      )}

      <Stack spacing={2}>
        {assessment.question_assessments.map((qa) => {
          const question = questionsById.get(qa.question_id);
          const met = qa.criterion_scores.filter((cs) => cs.met).length;

          return (
            <Accordion key={qa.question_id} className={styles.detail} disableGutters>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
                  <Chip label={`${qa.score}/10`} size="small" color="primary" />
                  <Typography className={styles.questionPrompt}>
                    {question?.prompt ?? 'Question'}
                  </Typography>
                  {qa.guardrail_flags.length > 0 && (
                    <Chip label="Flagged" size="small" color="warning" variant="outlined" />
                  )}
                </Stack>
              </AccordionSummary>

              <AccordionDetails>
                <Stack spacing={2}>
                  <Typography className="u-text-sm u-text-muted">
                    {met} of {qa.criterion_scores.length} criteria met
                  </Typography>

                  <Stack spacing={1}>
                    {qa.criterion_scores.map((cs) => (
                      <div key={cs.criterion} className={styles.criterion}>
                        {cs.met ? (
                          <CheckCircleIcon color="success" fontSize="small" />
                        ) : (
                          <CancelIcon color="disabled" fontSize="small" />
                        )}
                        <div>
                          <Typography className="u-text-sm">{cs.criterion}</Typography>
                          <Typography className="u-text-xs u-text-muted">
                            {cs.justification}
                          </Typography>
                        </div>
                      </div>
                    ))}
                  </Stack>

                  {qa.strengths.length > 0 && (
                    <div>
                      <Typography className="u-text-sm">Strengths</Typography>
                      <ul className={styles.list}>
                        {qa.strengths.map((item) => (
                          <li key={item}>
                            <Typography className="u-text-sm u-text-muted">{item}</Typography>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {qa.gaps.length > 0 && (
                    <div>
                      <Typography className="u-text-sm">Gaps</Typography>
                      <ul className={styles.list}>
                        {qa.gaps.map((item) => (
                          <li key={item}>
                            <Typography className="u-text-sm u-text-muted">{item}</Typography>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Stack>
              </AccordionDetails>
            </Accordion>
          );
        })}
      </Stack>
    </div>
  );
}
