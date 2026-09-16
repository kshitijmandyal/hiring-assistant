import { useState } from 'react';
import type { FormEvent } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { ErrorNotice } from '@/components/ErrorNotice';
import { useAppDispatch } from '@/store/hooks';
import { candidateStarted } from '@/store/sessionSlice';
import { useRegisterCandidateMutation } from './candidateApi';
import styles from './CandidateForm.module.scss';

const EMPTY_FORM = {
  full_name: '',
  email: '',
  phone: '',
  years_of_experience: '',
  desired_positions: '',
  location: '',
};

export function CandidateForm() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [registerCandidate, { isLoading, error }] = useRegisterCandidateMutation();
  const dispatch = useAppDispatch();

  const update = (field: keyof typeof EMPTY_FORM) => (value: string) =>
    setForm((previous) => ({ ...previous, [field]: value }));

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const candidate = await registerCandidate({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        years_of_experience: Number(form.years_of_experience),
        desired_positions: form.desired_positions
          .split(',')
          .map((position) => position.trim())
          .filter(Boolean),
        location: form.location.trim(),
      }).unwrap();
      dispatch(candidateStarted(candidate.id));
    } catch {
      // The mutation's `error` state renders the message; swallowing here only
      // prevents an unhandled rejection.
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} className={styles.form}>
      <Stack spacing={1}>
        <Typography variant="h5" component="h1">
          Technical screening
        </Typography>
        <Typography className="u-text-muted">
          A few details first, then questions matched to your experience.
        </Typography>
      </Stack>

      {/* A plain element, not Stack: MUI's emotion styles would override the
          grid layout this class defines at wider breakpoints. */}
      <div className={styles.fields}>
        <TextField
          label="Full name"
          value={form.full_name}
          onChange={(e) => update('full_name')(e.target.value)}
          className={styles.fullWidth}
          required
          fullWidth
        />
        <TextField
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => update('email')(e.target.value)}
          required
          fullWidth
        />
        <TextField
          label="Phone"
          value={form.phone}
          onChange={(e) => update('phone')(e.target.value)}
          placeholder="+91 98765 43210"
          helperText="Include your country code"
          required
          fullWidth
        />
        <TextField
          label="Years of experience"
          type="number"
          value={form.years_of_experience}
          onChange={(e) => update('years_of_experience')(e.target.value)}
          slotProps={{ htmlInput: { min: 0, max: 60, step: 0.5 } }}
          required
          fullWidth
        />
        <TextField
          label="Location"
          value={form.location}
          onChange={(e) => update('location')(e.target.value)}
          placeholder="Pune, India"
          required
          fullWidth
        />
        <TextField
          label="Desired position(s)"
          value={form.desired_positions}
          onChange={(e) => update('desired_positions')(e.target.value)}
          placeholder="Backend Engineer, Platform Engineer"
          helperText="Separate multiple roles with commas"
          className={styles.fullWidth}
          required
          fullWidth
        />
      </div>

      {error != null && <ErrorNotice error={error} />}

      <Button type="submit" variant="contained" size="large" disabled={isLoading}>
        {isLoading ? 'Saving…' : 'Continue'}
      </Button>
    </Box>
  );
}
