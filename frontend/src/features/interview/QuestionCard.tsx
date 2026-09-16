import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import { getKindLabel } from '@/helpers/interview';
import type { Question } from '@/types/api';
import styles from './QuestionCard.module.scss';

const ANSWER_MAX_LENGTH = 5000;

interface QuestionCardProps {
  question: Question;
  index: number;
  draft: string;
  answered: boolean;
  submitting: boolean;
  onDraftChange: (text: string) => void;
  onSubmit: () => void;
}

export function QuestionCard({
  question,
  index,
  draft,
  answered,
  submitting,
  onDraftChange,
  onSubmit,
}: QuestionCardProps) {
  const trimmed = draft.trim();
  const overLimit = draft.length > ANSWER_MAX_LENGTH;

  return (
    <section className={styles.card} aria-label={`Question ${index + 1}`}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography className={styles.number}>{index + 1}</Typography>
        <Chip label={getKindLabel(question.kind)} size="small" variant="outlined" />
        {answered && (
          <Chip
            icon={<CheckCircleIcon />}
            label="Answered"
            size="small"
            color="success"
            variant="outlined"
          />
        )}
      </Stack>

      <Typography className={styles.prompt}>{question.prompt}</Typography>

      <TextField
        value={draft}
        onChange={(e) => onDraftChange(e.target.value)}
        placeholder="Write your answer…"
        multiline
        minRows={4}
        fullWidth
        error={overLimit}
        helperText={
          overLimit
            ? `${draft.length} characters — the limit is ${ANSWER_MAX_LENGTH}.`
            : `${draft.length} / ${ANSWER_MAX_LENGTH}`
        }
      />

      <Stack direction="row" sx={{ justifyContent: 'flex-end' }}>
        <Button
          variant={answered ? 'outlined' : 'contained'}
          onClick={onSubmit}
          disabled={trimmed.length === 0 || overLimit || submitting}
        >
          {submitting ? 'Saving…' : answered ? 'Update answer' : 'Save answer'}
        </Button>
      </Stack>
    </section>
  );
}
