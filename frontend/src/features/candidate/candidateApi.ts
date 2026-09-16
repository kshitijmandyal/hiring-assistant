import { api } from '@/api/api';
import { ENDPOINTS } from '@/api/endpoints';
import type { Candidate, CandidateCreateRequest } from '@/types/api';

export const candidateApi = api.injectEndpoints({
  endpoints: (builder) => ({
    registerCandidate: builder.mutation<Candidate, CandidateCreateRequest>({
      query: (body) => ({
        url: ENDPOINTS.candidates.create(),
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Candidate'],
    }),

    getCandidate: builder.query<Candidate, string>({
      query: (candidateId) => ENDPOINTS.candidates.byId(candidateId),
      providesTags: (_result, _error, id) => [{ type: 'Candidate', id }],
    }),
  }),
});

export const { useRegisterCandidateMutation, useGetCandidateQuery } = candidateApi;
