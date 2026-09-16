import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Button from '@mui/material/Button';

import { getCorrelationId, getErrorMessage, isRetryable } from '@/helpers/errors';

interface ErrorNoticeProps {
  error: unknown;
  onRetry?: () => void;
}

export function ErrorNotice({ error, onRetry }: ErrorNoticeProps) {
  const correlationId = getCorrelationId(error);
  const canRetry = Boolean(onRetry) && isRetryable(error);

  return (
    <Alert
      severity="error"
      action={
        canRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
    >
      <AlertTitle>Something went wrong</AlertTitle>
      {getErrorMessage(error)}
      {correlationId && (
        <div className="u-text-xs u-text-muted" style={{ marginTop: 4 }}>
          Reference: {correlationId}
        </div>
      )}
    </Alert>
  );
}
