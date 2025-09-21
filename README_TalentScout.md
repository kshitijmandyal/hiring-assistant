
# TalentScout — Hiring Assistant (Streamlit)

## Overview
A Streamlit-based hiring assistant that collects candidate details and generates technical screening questions based on the candidate's declared tech stack. This repository is designed for the AI/ML Intern assignment.

## Features
- Collect candidate details: name, email, phone, experience, desired position, location, tech stack.
- Generate 3–5 technical questions per technology in the candidate's tech stack.
- Context-aware flow using Streamlit session state.
- Fallback handling and exit keywords.
- Optional Gemini AI integration if `GEMINI_API_KEY` is provided.
- Simulated (anonymized) in-memory storage of submissions.

## How to run locally
1. Clone or download the file.
2. Create virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install streamlit
# Optional: pip install google-generativeai python-dotenv
```

3. (Optional) To enable Gemini AI-powered question generation, set your API key in environment:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
# or on Windows: setx GEMINI_API_KEY "your-gemini-api-key-here"
```

4. Run the app:

```bash
streamlit run TalentScout_HiringAssistant_Streamlit.py
```

## Prompt design (summary)
- Information gathering prompt asks only for missing fields.
- Question generation prompt (for LLM) requests numbered concise questions spanning conceptual, coding, and debugging/design.
- When Gemini AI is not available, a deterministic local generator produces balanced question types per tech.

## Data handling
- All data is simulated and stored in-session only.
- Email and phone are anonymized when stored in the simulated submissions list.
- For a production system: use encrypted databases and follow GDPR; do not store sensitive personal data without consent.

## Extensions and bonus ideas
- Deploy to Streamlit Cloud, Heroku, or an EC2 instance; provide a live demo link.
- Add sentiment analysis via `textblob` or an LLM to detect candidate mood.
- Add multilingual support by translating prompts/responses via an LLM.
- Replace simulated storage with a secure DB and implement role-based access.

## Troubleshooting
- If the app shows errors about `google-generativeai`, install the package or unset `GEMINI_API_KEY` to use the local generator.

## Contact
This is a sample project for an assignment. Adapt and extend as needed.
