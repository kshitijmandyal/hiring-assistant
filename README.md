# TalentScout

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Claude](https://img.shields.io/badge/Claude-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/)
[![Postgres](https://img.shields.io/badge/Postgres-17-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org/)

Technical screening tool. An interviewer enters a candidate and their tech stack,
Claude writes questions for each technology, and the answers are graded against a
rubric generated alongside the questions.

## How it works

1. An interviewer signs in and adds a candidate.
2. They pick the candidate's technologies. Claude writes questions for each one,
   pitched at the seniority implied by their years of experience.
3. Each question ships with a rubric — two to four concrete things a strong answer
   contains.
4. The candidate gets a link scoped to that one interview and answers in their own time.
5. The interviewer finalises. Each answer is graded against its own rubric, with a
   per-criterion verdict and a summary for whoever reads it next.

Coverage is reported separately from score, so skipping a question doesn't read the
same as answering it badly.

## Architecture

```
backend/src/talentscout/
├── domain/        pure models and rules — imports no framework
├── interfaces.py  protocols: the seams everything else plugs into
├── services/      use cases, depending only on domain + interfaces
├── adapters/      claude/ and db/ — the only places those libraries appear
├── mappers/       all translation between layers
└── api/           routers, schemas, dependency wiring, error handlers
```

The rule that keeps it honest: `domain/` and `services/` may not import `anthropic`,
`sqlalchemy`, or `fastapi`. That's enforced by an `import-linter` contract in CI, not
by convention. It means the core logic runs in a plain script with no server and no
database.

The frontend mirrors the split — rendering in components, everything else in hooks and
helpers, all API paths in one file.

## Grading and guardrails

Candidates are graded on what they wrote, not on how much of it there was. Scoring is
per-criterion against the rubric the question was generated with.

Candidates can also see their own questions, and benefit from a higher score, so their
answers are treated as untrusted input:

- Answers are escaped and delimited before reaching the model, which is told to judge
  the contents rather than follow them.
- The returned grade is checked against the rubric that was actually sent. Invented or
  dropped criteria are discarded and flagged.
- A score the met criteria can't support is clamped.

The last two are plain code with no model output involved, so no amount of persuasion
in an answer can talk them out of it. Anything a guardrail touched is flagged in the
result rather than hidden, so the interviewer knows to read that answer themselves.

## Running it

Needs Docker, [uv](https://docs.astral.sh/uv/), and Node 20+.

```bash
git clone https://github.com/kshitijmandyal/hiring-assistant.git
cd hiring-assistant

docker compose up -d                    # postgres

cd backend
cp .env.example .env                    # add ANTHROPIC_API_KEY and JWT_SECRET
uv sync
uv run alembic upgrade head
uv run uvicorn talentscout.main:app --reload

cd ../frontend
npm install
npm run dev
```

Frontend on http://localhost:5173, API docs on http://localhost:8000/docs.

Generate a JWT secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Deploying

See [DEPLOY.md](DEPLOY.md). Render + Neon, both free, no card needed.

## Status

Working: auth, candidate intake, tech stack selection, persistence, the full API, and
the frontend flow.

Not yet verified: question generation and grading have not been run against a live
Anthropic key, so the prompts are untested in practice.

There are no tests yet. The protocol seams are there so they can be added without
restructuring anything.

## Licence

MIT — see [LICENSE](LICENSE).
