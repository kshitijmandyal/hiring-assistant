import { useState } from 'react';
import type { FormEvent } from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { ErrorNotice } from '@/components/ErrorNotice';
import { LoadingState } from '@/components/LoadingState';
import { useAppDispatch } from '@/store/hooks';
import { interviewStarted } from '@/store/sessionSlice';
import { useStartInterviewMutation } from './interviewApi';
import styles from './TechStackForm.module.scss';

const SUGGESTIONS = [
  'Python', 'TypeScript', 'JavaScript', 'Java', 'Go', 'Rust', 'C#',
  'React', 'Vue', 'Angular', 'Next.js', 'Node.js',
  'Django', 'FastAPI', 'Flask', 'Spring Boot', '.NET',
  'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
  'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes', 'Terraform',
  'PyTorch', 'TensorFlow', 'pandas', 'scikit-learn',
];

const MAX_TECHNOLOGIES = 10;

interface TechStackFormProps {
  candidateId: string;
}

export function TechStackForm({ candidateId }: TechStackFormProps) {
  const [technologies, setTechnologies] = useState<string[]>([]);
  const [perTechnology, setPerTechnology] = useState(4);
  const [startInterview, { isLoading, error }] = useStartInterviewMutation();
  const dispatch = useAppDispatch();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const interview = await startInterview({
        candidateId,
        body: { tech_stack: technologies, questions_per_technology: perTechnology },
      }).unwrap();
      dispatch(interviewStarted(interview.id));
    } catch {
      // Rendered from the mutation's `error` state; caught to avoid an
      // unhandled rejection.
    }
  };

  if (isLoading) {
    return (
      <LoadingState
        message="Writing your questions…"
        hint={`Generating ${perTechnology} questions for each of ${technologies.length} technologies. This usually takes under a minute.`}
      />
    );
  }

  return (
    <Box component="form" onSubmit={handleSubmit} className={styles.form}>
      <Stack spacing={1}>
        <Typography variant="h5" component="h1">
          Your tech stack
        </Typography>
        <Typography className="u-text-muted">
          Pick what you know well. Questions are written for each one.
        </Typography>
      </Stack>

      <Autocomplete
        multiple
        freeSolo
        options={SUGGESTIONS}
        value={technologies}
        onChange={(_, value) => setTechnologies(value.slice(0, MAX_TECHNOLOGIES))}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Technologies"
            placeholder={technologies.length ? '' : 'Start typing…'}
            helperText={`${technologies.length} of ${MAX_TECHNOLOGIES}`}
          />
        )}
      />

      <Stack spacing={1}>
        <Typography component="label" id="per-tech-label" className="u-text-sm">
          Questions per technology: <strong>{perTechnology}</strong>
        </Typography>
        <Slider
          value={perTechnology}
          onChange={(_, value) => setPerTechnology(value as number)}
          min={3}
          max={6}
          step={1}
          marks
          aria-labelledby="per-tech-label"
        />
        <Typography className="u-text-xs u-text-muted">
          {technologies.length * perTechnology} questions in total
        </Typography>
      </Stack>

      {error != null && <ErrorNotice error={error} />}

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={technologies.length === 0}
      >
        Generate questions
      </Button>
    </Box>
  );
}
