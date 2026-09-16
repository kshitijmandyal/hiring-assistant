import { api } from '@/api/api';
import { ENDPOINTS } from '@/api/endpoints';
import type {
  CurrentUser,
  Invite,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from '@/types/api';

export const authApi = api.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<TokenResponse, LoginRequest>({
      query: (body) => ({ url: ENDPOINTS.auth.login(), method: 'POST', body }),
      invalidatesTags: ['User'],
    }),

    register: builder.mutation<CurrentUser, RegisterRequest>({
      query: (body) => ({ url: ENDPOINTS.auth.register(), method: 'POST', body }),
    }),

    logout: builder.mutation<void, string>({
      query: (refreshToken) => ({
        url: ENDPOINTS.auth.logout(),
        method: 'POST',
        body: { refresh_token: refreshToken },
      }),
    }),

    me: builder.query<CurrentUser, void>({
      query: () => ENDPOINTS.auth.me(),
      providesTags: ['User'],
    }),

    createInvite: builder.mutation<Invite, string>({
      query: (interviewId) => ({
        url: ENDPOINTS.interviews.invite(interviewId),
        method: 'POST',
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useMeQuery,
  useCreateInviteMutation,
} = authApi;
