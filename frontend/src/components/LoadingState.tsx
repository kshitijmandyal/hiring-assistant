import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';

interface LoadingStateProps {
  message?: string;
  /** Shown when the wait is long enough that users need reassurance. */
  hint?: string;
}

export function LoadingState({ message = 'Loading…', hint }: LoadingStateProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 12,
        padding: '3rem 1rem',
      }}
      role="status"
      aria-live="polite"
    >
      <CircularProgress size={28} />
      <Typography>{message}</Typography>
      {hint && (
        <Typography className="u-text-sm u-text-muted u-text-center">{hint}</Typography>
      )}
    </div>
  );
}
