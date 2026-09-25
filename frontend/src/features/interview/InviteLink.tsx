import { useState } from 'react';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { ErrorNotice } from '@/components/ErrorNotice';
import { useCreateInviteMutation } from './interviewApi';
import styles from './InviteLink.module.scss';

interface InviteLinkProps {
  interviewId: string;
}

export function InviteLink({ interviewId }: InviteLinkProps) {
  const [createInvite, { data, isLoading, error }] = useCreateInviteMutation();
  const [copied, setCopied] = useState(false);

  const link = data ? `${window.location.origin}/?invite=${data.invite_token}` : '';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard blocked (insecure context or denied permission) — the field is
      // selectable, so the user can still copy manually.
    }
  };

  return (
    <section className={styles.card}>
      <Stack spacing={1}>
        <Typography variant="h6" component="h2">
          Invite the candidate
        </Typography>
        <Typography className="u-text-sm u-text-muted">
          A link that opens only this interview. It cannot be used to reach anything else.
        </Typography>
      </Stack>

      {error != null && <ErrorNotice error={error} />}

      {data ? (
        <Stack spacing={1.5}>
          <TextField
            value={link}
            slotProps={{ htmlInput: { readOnly: true, spellCheck: false } }}
            fullWidth
            onFocus={(e) => e.target.select()}
          />
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Button variant="outlined" onClick={() => void handleCopy()}>
              {copied ? 'Copied' : 'Copy link'}
            </Button>
            <Typography className="u-text-xs u-text-muted">
              Expires in {data.expires_in_days} days
            </Typography>
          </Stack>
          <Alert severity="info">
            Anyone with this link can answer the interview, so send it to the candidate
            directly.
          </Alert>
        </Stack>
      ) : (
        <Button
          variant="contained"
          onClick={() => void createInvite(interviewId)}
          disabled={isLoading}
        >
          {isLoading ? 'Creating…' : 'Create invite link'}
        </Button>
      )}
    </section>
  );
}
