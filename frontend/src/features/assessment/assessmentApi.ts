import { api } from '@/api/api';
import { ENDPOINTS } from '@/api/endpoints';
import type { Assessment } from '@/types/api';

export const assessmentApi = api.injectEndpoints({
  endpoints: (builder) => ({
    finaliseInterview: builder.mutation<Assessment, string>({
      query: (interviewId) => ({
        url: ENDPOINTS.interviews.assessment(interviewId),
        method: 'POST',
      }),
      // Finalising closes the interview, so its cached copy is now stale.
      invalidatesTags: (_result, _error, interviewId) => [
        { type: 'Interview', id: interviewId },
        'Assessment',
      ],
    }),

    getAssessment: builder.query<Assessment, string>({
      query: (interviewId) => ENDPOINTS.interviews.assessment(interviewId),
      providesTags: (_result, _error, id) => [{ type: 'Assessment', id }],
    }),
  }),
});

export const { useFinaliseInterviewMutation, useGetAssessmentQuery } = assessmentApi;
