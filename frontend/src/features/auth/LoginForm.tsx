import { useState } from 'react';
import type { FormEvent } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { ErrorNotice } from '@/components/ErrorNotice';
import { useAppDispatch } from '@/store/hooks';
import { credentialsReceived } from '@/store/authSlice';
import { useLoginMutation, useRegisterMutation } from './authApi';
import styles from './LoginForm.module.scss';

const PASSWORD_MIN_LENGTH = 12;

export function LoginForm() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');

  const [login, loginState] = useLoginMutation();
  const [register, registerState] = useRegisterMutation();
  const dispatch = useAppDispatch();

  const isRegister = mode === 'register';
  const pending = loginState.isLoading || registerState.isLoading;
  const error = loginState.error ?? registerState.error;
  const passwordTooShort = password.length > 0 && password.length < PASSWORD_MIN_LENGTH;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      if (isRegister) {
        await register({ email, full_name: fullName, password }).unwrap();
      }
      const tokens = await login({ email, password }).unwrap();
      dispatch(
        credentialsReceived({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          role: 'interviewer',
        }),
      );
    } catch {
      // Rendered from the mutation error state; caught to avoid an unhandled rejection.
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} className={styles.form}>
      <Stack spacing={1}>
        <Typography variant="h5" component="h1">
          TalentScout
        </Typography>
        <Typography className="u-text-muted">
          Sign in to set up a screening and review results.
        </Typography>
      </Stack>

      <Tabs
        value={mode}
        onChange={(_, value: 'login' | 'register') => setMode(value)}
        aria-label="Sign in or create an account"
      >
        <Tab label="Sign in" value="login" />
        <Tab label="Create account" value="register" />
      </Tabs>

      <Stack spacing={2}>
        {isRegister && (
          <TextField
            label="Your name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            fullWidth
          />
        )}
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          fullWidth
        />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={isRegister && passwordTooShort}
          helperText={
            isRegister ? `At least ${PASSWORD_MIN_LENGTH} characters` : undefined
          }
          required
          fullWidth
        />
      </Stack>

      {error != null && <ErrorNotice error={error} />}

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={pending || (isRegister && passwordTooShort)}
      >
        {pending ? 'Working…' : isRegister ? 'Create account' : 'Sign in'}
      </Button>
    </Box>
  );
}
