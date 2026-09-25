import { api } from '@/api/api';
import { ENDPOINTS } from '@/api/endpoints';
import type {
  AnswerSubmitRequest,
  Interview,
  InterviewStartRequest,
  Invite,
} from '@/types/api';

export const interviewApi = api.injectEndpoints({
  endpoints: (builder) => ({
    startInterview: builder.mutation<
      Interview,
      { candidateId: string; body: InterviewStartRequest }
    >({
      query: ({ candidateId, body }) => ({
        url: ENDPOINTS.candidates.interviews(candidateId),
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Interview'],
    }),

    createInvite: builder.mutation<Invite, string>({
      query: (interviewId) => ({
        url: ENDPOINTS.interviews.invite(interviewId),
        method: 'POST',
      }),
    }),

    getInterview: builder.query<Interview, string>({
      query: (interviewId) => ENDPOINTS.interviews.byId(interviewId),
      providesTags: (_result, _error, id) => [{ type: 'Interview', id }],
    }),

    submitAnswer: builder.mutation<
      Interview,
      { interviewId: string; body: AnswerSubmitRequest }
    >({
      query: ({ interviewId, body }) => ({
        url: ENDPOINTS.interviews.answers(interviewId),
        method: 'POST',
        body,
      }),
      // The response is the updated interview, so write it straight into the cache
      // rather than invalidating and refetching.
      async onQueryStarted({ interviewId }, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          dispatch(
            interviewApi.util.updateQueryData('getInterview', interviewId, (draft) => {
              Object.assign(draft, data);
            }),
          );
        } catch {
          // The mutation's own error state drives the UI; nothing to do here.
        }
      },
    }),
  }),
});

export const {
  useStartInterviewMutation,
  useCreateInviteMutation,
  useGetInterviewQuery,
  useSubmitAnswerMutation,
} = interviewApi;
