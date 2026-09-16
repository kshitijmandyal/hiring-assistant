/**
 * Typed Redux hooks. Use these everywhere instead of the raw `useDispatch` and
 * `useSelector`, which return untyped values and need a generic at each call site.
 */

import { useDispatch, useSelector } from 'react-redux';

import type { AppDispatch, RootState } from './store';

export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
