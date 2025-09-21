"""
TalentScout Hiring Assistant - Streamlit App
File: TalentScout_HiringAssistant_Streamlit.py

This single-file app contains:
 - Streamlit UI for candidate-chat interaction
 - Prompt templates for information gathering & technical question generation
 - Optional OpenAI integration (use OPENAI_API_KEY env var)
 - In-memory (simulated) storage of submissions (anonymized)
 - README stored as README_MD variable at the bottom

Run: `streamlit run TalentScout_HiringAssistant_Streamlit.py`

Dependencies: streamlit, google-generativeai (optional), python-dotenv (optional)

"""

import os
import re
import json
import time
from typing import List, Dict, Tuple, Any, Union

try:
    import streamlit as st
except Exception as e:
    raise ImportError("Streamlit is required. Install with: pip install streamlit")

# Optional Gemini AI integration
USE_GEMINI = False
try:
    import google.generativeai as genai
    # Check both possible environment variable names and Streamlit secrets
    api_key = None
    if hasattr(st, 'secrets'):
        api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if api_key:
        # Use getattr to handle different API versions
        configure_func = getattr(genai, 'configure', None)
        if configure_func:
            configure_func(api_key=api_key)
            USE_GEMINI = True
except Exception:
    # google-generativeai not installed or key not present — we'll use a local template-based generator
    USE_GEMINI = False

# -----------------------------
# Configuration
# -----------------------------
EXIT_KEYWORDS = {"exit", "quit", "bye", "stop", "end"}
FALLBACK_MESSAGE = (
    "I'm here to help! I can:\n"
    "• Collect your details (use 'Provide Details' button)\n"
    "• Generate technical questions based on your tech stack\n"
    "• Answer questions about filling the form (try asking 'What do I write in desired positions?')\n\n"
    "Type 'help' for commands or ask me about any form field!"
)

# Simulated (anonymized) storage — in-memory.
# For a real project, store securely in a database and follow GDPR best practices.
SUBMISSIONS = []

# Basic validation regexes
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[+\d][\d\s-]{6,}$")

# -----------------------------
# Prompt Templates & Helpers
# -----------------------------

def build_info_prompt(session_context: Dict[str, Any]) -> str:
    """Return a short, clear prompt that requests missing candidate info."""
    required = [
        ("full_name", "Full Name"),
        ("email", "Email Address"),
        ("phone", "Phone Number"),
        ("years_exp", "Years of Experience"),
        ("desired_positions", "Desired Position(s)"),
        ("location", "Current Location"),
        ("tech_stack", "Tech Stack (comma-separated)"),
    ]
    missing = [label for key, label in required if not session_context.get(key)]
    if not missing:
        return "All candidate info collected. Would you like me to generate technical questions based on the provided tech stack?"
    return "Please provide: " + ", ".join(missing)


def gemini_generate(prompt: str, max_tokens: int = 300) -> str:
    """Call Gemini completion (if available). Wraps call safely."""
    if not USE_GEMINI:
        raise RuntimeError("Gemini integration not enabled. Set GEMINI_API_KEY to enable.")
    
    start_time = time.time()
    st.info("🤖 Calling Gemini AI... This may take 10-30 seconds.")
    
    try:
        # Import locally to handle type checking issues
        import google.generativeai as local_genai
        
        # Use getattr to avoid linter issues with newer API
        GenerativeModel = getattr(local_genai, 'GenerativeModel', None)
        GenerationConfig = getattr(local_genai, 'GenerationConfig', None)
        
        if not GenerativeModel or not GenerationConfig:
            raise RuntimeError("Gemini API classes not available")
        
        # Try different model names to find working one
        models_to_try = [
            'models/gemini-1.5-flash', 
            'models/gemini-1.5-pro', 
            'models/gemini-2.0-flash',
            'models/gemini-2.5-flash'
        ]
        
        model = None
        for model_name in models_to_try:
            try:
                model = GenerativeModel(model_name)
                break
            except Exception:
                continue
        
        if not model:
            raise RuntimeError("No working Gemini model found")
            
        # Show progress
        with st.spinner('Generating questions with AI...'):
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.2,
                )
            )
        
        elapsed_time = time.time() - start_time
        st.success(f"✅ AI response received in {elapsed_time:.2f} seconds")
        
        return response.text.strip() if hasattr(response, 'text') and response.text else ""
    except Exception as e:
        elapsed_time = time.time() - start_time
        st.error(f"❌ Gemini request failed after {elapsed_time:.2f} seconds: {e}")
        st.info("🔄 Falling back to local question generator...")
        return ""


def get_difficulty_level(years_exp: str) -> str:
    """Determine question difficulty based on years of experience."""
    try:
        years = float(years_exp) if years_exp else 0
        if years >= 5:
            return "advanced"
        elif years >= 2:
            return "intermediate"
        else:
            return "beginner"
    except:
        return "beginner"


def generate_questions_local(tech: str, count: int = 4, difficulty: str = "intermediate") -> List[str]:
    """Generate simple question templates for a single technology locally (no LLM).

    This is used when OpenAI is not configured. The questions are deterministic and
    cover conceptual, practical, debugging, and design aspects where applicable.
    """
    t = tech.strip().lower()
    qs = []

    # Basic general template
    qs.append(f"Explain a recent project where you used {tech}. What was your role and the biggest challenge?")
    if "python" in t:
        qs += [
            "Describe the difference between deep and shallow copies in Python. Give examples.",
            "How do you optimize Python code for performance? Name tools or techniques you use.",
        ]
    elif "django" in t or "flask" in t:
        qs += [
            f"How do you handle authentication and authorization in {tech}?",
            f"Explain how you structure a medium-sized web application using {tech}.",
        ]
    elif "sql" in t or "mysql" in t or "postgres" in t or "postgresql" in t:
        qs += [
            "Write a SQL query to find duplicate rows in a table and remove them.",
            "Explain indexes. When do indexes hurt performance?",
        ]
    elif "aws" in t or "gcp" in t or "azure" in t:
        qs += [
            f"Which services do you use for deploying a scalable API on {tech}? Why?",
            "How do you design for high availability and disaster recovery in cloud?",
        ]
    elif "pytorch" in t or "tensorflow" in t or "keras" in t:
        qs += [
            "Explain the difference between model.train() and model.eval().",
            "How do you prevent overfitting? List techniques and give examples.",
        ]
    elif "react" in t or "vue" in t or "angular" in t:
        qs += [
            "Explain how state management works in your chosen frontend framework.",
            "How do you optimize rendering performance for complex UI components?",
        ]
    else:
        # Generic technical questions
        qs += [
            f"What are the key concepts of {tech}?",
            f"Describe a debugging approach you follow when a {tech} based solution fails in production.",
        ]

    # Trim/extend to requested count
    if len(qs) >= count:
        return qs[:count]
    # add filler question variants if too few
    i = 1
    while len(qs) < count:
        qs.append(f"Additional question {i} about {tech}.")
        i += 1
    return qs


def evaluate_candidate_responses(responses: Dict[str, str], tech_stack: List[str]) -> Dict[str, Any]:
    """Simple evaluation of candidate responses using keyword matching and length heuristics."""
    if not responses:
        return {"total_score": 0, "max_score": 0, "details": {}}
    
    evaluation = {
        "total_score": 0,
        "max_score": len(responses) * 10,  # Max 10 points per question
        "details": {}
    }
    
    for response_key, response in responses.items():
        if not response.strip():
            evaluation["details"][response_key] = {"score": 0, "feedback": "No response provided"}
            continue
            
        score = 0
        feedback_points = []
        
        # Length-based scoring (basic completeness)
        if len(response.strip()) > 50:
            score += 3
            feedback_points.append("Good response length")
        elif len(response.strip()) > 20:
            score += 2
            feedback_points.append("Adequate response length")
        else:
            score += 1
            feedback_points.append("Brief response")
        
        # Keyword-based scoring for technical terms
        tech_keywords = ["algorithm", "data", "code", "function", "method", "class", 
                        "performance", "optimization", "debugging", "testing", "design",
                        "architecture", "database", "api", "framework", "library"]
        
        keyword_count = sum(1 for keyword in tech_keywords if keyword.lower() in response.lower())
        if keyword_count >= 3:
            score += 4
            feedback_points.append("Good use of technical terminology")
        elif keyword_count >= 1:
            score += 2
            feedback_points.append("Some technical terminology used")
        
        # Example/experience mentioned
        experience_indicators = ["project", "experience", "used", "implemented", "worked", "built"]
        if any(indicator in response.lower() for indicator in experience_indicators):
            score += 3
            feedback_points.append("Mentions practical experience")
        
        evaluation["details"][response_key] = {
            "score": min(score, 10),  # Cap at 10
            "feedback": "; ".join(feedback_points) if feedback_points else "Basic response"
        }
        evaluation["total_score"] += min(score, 10)
    
    return evaluation


def generate_questions_for_stack(tech_stack: List[str], per_tech: int = 4, years_exp: str = "", use_ai: Union[bool, None] = None) -> Dict[str, List[str]]:
    """Generate question sets per technology. Tries Gemini if enabled, otherwise local generator."""
    difficulty = get_difficulty_level(years_exp)
    results = {}
    
    # Allow override of AI usage
    use_gemini = USE_GEMINI if use_ai is None else (use_ai and USE_GEMINI)
    
    total_start_time = time.time()
    
    for i, tech in enumerate(tech_stack, 1):
        tech_start_time = time.time()
        st.info(f"📝 Generating questions for {tech} ({i}/{len(tech_stack)})...")
        
        if use_gemini:
            difficulty_prompt = f" Generate {difficulty}-level questions suitable for someone with {years_exp or 'some'} years of experience." if years_exp else ""
            prompt = (
                f"You are an expert technical interviewer. For the technology '{tech}', produce {per_tech} concise, clear technical questions that span conceptual, coding, and debugging/design.{difficulty_prompt} "
                "Return them as a numbered list only."
            )
            out = gemini_generate(prompt, max_tokens=300)
            # crude parsing: split into lines and clean numbers
            lines = [re.sub(r'^\s*\d+\.?\s*', '', line).strip() for line in out.splitlines() if line.strip()]
            if len(lines) < per_tech:
                # fallback to local fill
                st.info(f"🔄 AI generated {len(lines)} questions, filling remaining with local generator...")
                lines += generate_questions_local(tech, per_tech - len(lines), difficulty)
            results[tech] = lines[:per_tech]
        else:
            st.info(f"⚡ Using fast local generator for {tech}...")
            results[tech] = generate_questions_local(tech, per_tech, difficulty)
        
        tech_elapsed = time.time() - tech_start_time
        st.success(f"✅ {tech} questions ready in {tech_elapsed:.2f} seconds")
    
    total_elapsed = time.time() - total_start_time
    st.success(f"🎉 All questions generated in {total_elapsed:.2f} seconds total!")
    
    return results


# -----------------------------
# Streamlit App UI
# -----------------------------

def init_state():
    if "context" not in st.session_state:
        st.session_state.context = {
            "full_name": "",
            "email": "",
            "phone": "",
            "years_exp": "",
            "desired_positions": "",
            "location": "",
            "tech_stack": [],
            "conversation": [],
        }
    if "submissions" not in st.session_state:
        st.session_state.submissions = []


def validate_and_store_submission(context: Dict[str, Any]):
    # Minimal validation
    ok = True
    email = context.get("email")
    phone = context.get("phone")
    
    if email and not EMAIL_RE.match(str(email)):
        ok = False
    if phone and not PHONE_RE.match(str(phone)):
        ok = False
        
    if ok:
        # store an anonymized copy (mask phone and email partially)
        stored = dict(context)
        if stored.get("email"):
            e = stored["email"]
            parts = e.split("@")
            stored["email"] = parts[0][:2] + "***@" + parts[1]
        if stored.get("phone"):
            p = re.sub(r"\D", "", stored["phone"])
            stored["phone"] = ("+" + p[:-4] + "****") if len(p) > 4 else "****"
        stored["timestamp"] = time.time()
        st.session_state.submissions.append(stored)
        return True
    return False


def sidebar_info():
    st.sidebar.header("TalentScout - Hiring Assistant")
    st.sidebar.markdown("Built for: AI/ML Intern Assignment (Streamlit) — Demo")
    st.sidebar.markdown("\n**Exit keywords:** `exit`, `quit`, `bye`, `stop`\n")
    st.sidebar.markdown("**Gemini AI:** " + ("Enabled" if USE_GEMINI else "Disabled (local generator)"))
    
    if USE_GEMINI:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🚀 Performance Tips")
        st.sidebar.markdown("**⚡ Fast Local:** Instant results")
        st.sidebar.markdown("**🤖 AI Generation:** 10-30 seconds")
        st.sidebar.markdown("*Tip: Use 'generate ai' in chat for AI questions*")
    
    # Export functionality
    if st.session_state.submissions:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Export Data")
        if st.sidebar.button("Export All Submissions"):
            export_data = json.dumps(st.session_state.submissions, indent=2, default=str)
            st.sidebar.download_button(
                label="Download JSON",
                data=export_data,
                file_name=f"candidate_submissions_{int(time.time())}.json",
                mime="application/json"
            )
    if st.sidebar.button("Reset Conversation"):
        st.session_state.context = {
            "full_name": "",
            "email": "",
            "phone": "",
            "years_exp": "",
            "desired_positions": "",
            "location": "",
            "tech_stack": [],
            "conversation": [],
        }
        st.rerun()


def main():
    st.set_page_config(page_title="TalentScout Hiring Assistant", layout="centered")
    init_state()
    sidebar_info()

    st.title("TalentScout — Hiring Assistant")
    st.write("Hello! I'm TalentScout's initial screening assistant. I will collect some details and generate technical questions based on your tech stack.")

    # show conversation
    for msg in st.session_state.context.get("conversation", []):
        if msg["role"] == "bot":
            st.info(msg["text"])
        else:
            st.write(f"**You:** {msg['text']}")

    # Quick action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    if col1.button("Provide Details"):
        st.session_state._show_details = True
    if col2.button("Enter Tech Stack"):
        st.session_state._show_tech = True
    if col3.button("Generate Questions"):
        st.session_state._show_generate = True

    # Detail form
    if st.session_state.get("_show_details"):
        with st.form("details_form"):
            st.subheader("Candidate Details")
            full_name = st.text_input("Full Name", value=st.session_state.context.get("full_name", ""))
            email = st.text_input("Email", value=st.session_state.context.get("email", ""))
            phone = st.text_input("Phone", value=st.session_state.context.get("phone", ""))
            years = st.text_input("Years of Experience", value=st.session_state.context.get("years_exp", ""))
            desired = st.text_input("Desired Position(s)", value=st.session_state.context.get("desired_positions", ""))
            location = st.text_input("Current Location", value=st.session_state.context.get("location", ""))
            submitted = st.form_submit_button("Save Details")
            if submitted:
                st.session_state.context.update({
                    "full_name": (full_name or "").strip(),
                    "email": (email or "").strip(),
                    "phone": (phone or "").strip(),
                    "years_exp": (years or "").strip(),
                    "desired_positions": (desired or "").strip(),
                    "location": (location or "").strip(),
                })
                st.session_state.context["conversation"].append({"role": "bot", "text": "Details saved."})
                ok = validate_and_store_submission(st.session_state.context)
                if ok:
                    st.success("Saved (simulated) — details stored anonymously.")
                else:
                    st.warning("Saved locally in session, but some fields may be invalid (email/phone).")
                st.session_state._show_details = False
                st.rerun()

    # Tech stack input
    if st.session_state.get("_show_tech"):
        with st.form("tech_form"):
            st.subheader("Tech Stack Declaration")
            st.write("List the technologies you're proficient in. Use commas to separate multiple items. Example: Python, Django, PostgreSQL, AWS")
            text = st.text_area("Tech Stack", value=", ".join(st.session_state.context.get("tech_stack", [])))
            submitted = st.form_submit_button("Save Tech Stack")
            if submitted:
                techs = [t.strip() for t in text.split(",") if t.strip()]
                st.session_state.context["tech_stack"] = techs
                st.session_state.context["conversation"].append({"role": "bot", "text": f"Tech stack recorded: {', '.join(techs)}"})
                st.success("Tech stack saved.")
                st.session_state._show_tech = False
                st.rerun()

    # Manual generation
    if st.session_state.get("_show_generate"):
        techs = st.session_state.context.get("tech_stack")
        if not techs:
            st.warning("No tech stack provided. Enter tech stack first.")
        else:
            st.subheader("Question Generation Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                per = st.slider("Questions per technology", 3, 6, 4)
            with col2:
                generation_method = st.radio(
                    "Generation Method:",
                    ["⚡ Fast Local (Instant)", "🤖 AI Powered (Slower but better)"],
                    help="Local is instant but basic. AI is slower (10-30s) but creates more sophisticated questions."
                )
            
            use_ai = "🤖 AI Powered" in generation_method
            
            if st.button("Generate now"):
                st.session_state.context["conversation"].append({"role": "bot", "text": "Generating questions..."})
                st.session_state._generation_settings = {"per_tech": per, "use_ai": use_ai}
                st.rerun()

    # Handle pending generation
    if st.session_state.get("_generation_settings"):
        settings = st.session_state._generation_settings
        techs = st.session_state.context.get("tech_stack")
        if techs:
            results = generate_questions_for_stack(
                techs, 
                settings["per_tech"], 
                st.session_state.context.get("years_exp", ""),
                settings["use_ai"]
            )
            st.session_state.last_generated = results
            st.session_state.context["conversation"].append({"role": "bot", "text": "Generated technical questions."})
            del st.session_state._generation_settings
            st.rerun()

    # If generation flag not set but we have tech stack and no questions yet, offer to generate
    if st.session_state.context.get("tech_stack") and not st.session_state.get("last_generated"):
        st.info("🎯 Ready to generate questions for your tech stack!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Quick Generate (Fast)", help="Uses local generator - instant results"):
                per = 4
                techs = st.session_state.context.get("tech_stack")
                results = generate_questions_for_stack(techs, per, st.session_state.context.get("years_exp", ""), use_ai=False)
                st.session_state.last_generated = results
                st.session_state.context["conversation"].append({"role": "bot", "text": "Generated technical questions using fast local generator."})
                st.rerun()
        
        with col2:
            if st.button("🤖 AI Generate (Better)", help="Uses Gemini AI - takes 10-30 seconds but higher quality"):
                if not USE_GEMINI:
                    st.warning("Gemini AI not configured. Set GEMINI_API_KEY environment variable to use AI generation.")
                else:
                    per = 4
                    techs = st.session_state.context.get("tech_stack")
                    results = generate_questions_for_stack(techs, per, st.session_state.context.get("years_exp", ""), use_ai=True)
                    st.session_state.last_generated = results
                    st.session_state.context["conversation"].append({"role": "bot", "text": "Generated technical questions using Gemini AI."})
                    st.rerun()

    # Display generated questions if present
    if st.session_state.get("last_generated"):
        st.subheader("Generated Technical Questions")
        
        # Initialize responses storage if not exists
        if "candidate_responses" not in st.session_state:
            st.session_state.candidate_responses = {}
        
        # Display questions with response collection
        for tech, qs in st.session_state.last_generated.items():
            st.markdown(f"**{tech}**")
            for i, q in enumerate(qs, 1):
                st.write(f"{i}. {q}")
                
                # Add response text area for each question
                response_key = f"{tech}_{i}"
                response = st.text_area(
                    f"Your answer to {tech} Question {i}:",
                    value=st.session_state.candidate_responses.get(response_key, ""),
                    key=f"response_{response_key}",
                    height=100,
                    placeholder="Type your answer here..."
                )
                st.session_state.candidate_responses[response_key] = response
            st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save All Responses"):
                # Store responses in context
                st.session_state.context["responses"] = st.session_state.candidate_responses
                st.success("All responses saved!")
                
        with col2:
            if st.button("Finalize & Finish Conversation"):
                # Store final responses in context before finishing
                st.session_state.context["responses"] = st.session_state.candidate_responses
                
                # Evaluate responses
                evaluation = evaluate_candidate_responses(
                    st.session_state.candidate_responses, 
                    st.session_state.context.get("tech_stack", [])
                )
                st.session_state.context["evaluation"] = evaluation
                
                st.success("Thank you — the conversation is concluded. We will email next steps (simulated).")
                st.session_state.context["conversation"].append({"role": "bot", "text": "Conversation concluded. Thank you!"})
                # store final submit snapshot
                _ = validate_and_store_submission(st.session_state.context)
                
                # Show completion summary with evaluation
                st.subheader("Interview Summary & Evaluation")
                col_info, col_eval = st.columns(2)
                
                with col_info:
                    st.write("**Candidate Information:**")
                    st.write(f"• **Name:** {st.session_state.context.get('full_name', 'N/A')}")
                    st.write(f"• **Email:** {st.session_state.context.get('email', 'N/A')}")
                    st.write(f"• **Experience:** {st.session_state.context.get('years_exp', 'N/A')} years")
                    st.write(f"• **Tech Stack:** {', '.join(st.session_state.context.get('tech_stack', []))}")
                
                with col_eval:
                    st.write("**Technical Assessment:**")
                    answered = len([r for r in st.session_state.candidate_responses.values() if r.strip()])
                    total_questions = len(st.session_state.candidate_responses)
                    st.write(f"• **Questions Answered:** {answered}/{total_questions}")
                    
                    if evaluation["max_score"] > 0:
                        score_percentage = (evaluation["total_score"] / evaluation["max_score"]) * 100
                        st.write(f"• **Score:** {evaluation['total_score']}/{evaluation['max_score']} ({score_percentage:.1f}%)")
                        
                        # Simple rating based on score
                        if score_percentage >= 80:
                            st.write("• **Rating:** ⭐⭐⭐⭐⭐ Excellent")
                        elif score_percentage >= 60:
                            st.write("• **Rating:** ⭐⭐⭐⭐ Good")
                        elif score_percentage >= 40:
                            st.write("• **Rating:** ⭐⭐⭐ Average")
                        else:
                            st.write("• **Rating:** ⭐⭐ Needs Improvement")
                
                st.session_state.last_generated = None

    # Free text input area (chat-like)
    st.write("---")
    st.write("Or chat freely below. (Type 'help' for quick commands.)")
    
    # Use a form to prevent multiple submissions
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message:", key="chat_input")
        submitted = st.form_submit_button("Send")
    
    if submitted and user_input:
        text = user_input.strip()
        if text:  # Only process non-empty messages
            st.session_state.context["conversation"].append({"role": "user", "text": text})

            # check exit
            if text.lower() in EXIT_KEYWORDS:
                st.session_state.context["conversation"].append({"role": "bot", "text": "Thanks for your time — ending the conversation."})
                st.rerun()

            # simple commands
            elif text.lower() == "help":
                st.session_state.context["conversation"].append({"role": "bot", "text": "Commands:\n- Provide Details\n- Enter Tech Stack\n- Generate Questions\n- exit/quit to end\n\nYou can also ask questions like 'What do I write in desired positions?' or 'How do I fill the tech stack?'"})
                st.rerun()

            # Handle form help questions
            else:
                text_lower = text.lower()
                handled = False
                
                if any(keyword in text_lower for keyword in ["desired position", "position", "job title", "role"]):
                    help_text = (
                        "For **Desired Position(s)**, write the job roles you're interested in. Examples:\n"
                        "• AI/ML Engineer Intern\n"
                        "• Software Engineer\n"
                        "• Data Scientist\n"
                        "• Full Stack Developer\n"
                        "• Python Developer, Backend Engineer (for multiple positions)\n\n"
                        "Match it with your tech stack and experience level!"
                    )
                    st.session_state.context["conversation"].append({"role": "bot", "text": help_text})
                    handled = True
                
                elif any(keyword in text_lower for keyword in ["tech stack", "technology", "programming", "skills"]):
                    help_text = (
                        "For **Tech Stack**, list technologies you know separated by commas. Examples:\n"
                        "• Python, Django, PostgreSQL, AWS\n"
                        "• JavaScript, React, Node.js, MongoDB\n"
                        "• Java, Spring Boot, MySQL\n"
                        "• Python, TensorFlow, Pandas, scikit-learn\n\n"
                        "Include programming languages, frameworks, databases, and tools you're proficient in!"
                    )
                    st.session_state.context["conversation"].append({"role": "bot", "text": help_text})
                    handled = True
                
                elif any(keyword in text_lower for keyword in ["experience", "years", "how long"]):
                    help_text = (
                        "For **Years of Experience**, enter a number representing your total programming/technical experience:\n"
                        "• 0 or 0.5 for beginners/students\n"
                        "• 1-2 for junior level\n"
                        "• 3-5 for mid-level\n"
                        "• 5+ for senior level\n\n"
                        "Include internships, projects, and professional work!"
                    )
                    st.session_state.context["conversation"].append({"role": "bot", "text": help_text})
                    handled = True

                elif any(keyword in text_lower for keyword in ["email", "phone", "contact"]):
                    help_text = (
                        "For contact information:\n"
                        "• **Email**: Use a professional email address (e.g., john.doe@email.com)\n"
                        "• **Phone**: Include country code if international (e.g., +1 123-456-7890)\n"
                        "• **Location**: City, State/Country (e.g., San Francisco, CA or Mumbai, India)"
                    )
                    st.session_state.context["conversation"].append({"role": "bot", "text": help_text})
                    handled = True
                
                elif any(keyword in text_lower for keyword in ["name", "full name"]):
                    help_text = (
                        "For **Full Name**, enter your complete name as you'd like it to appear professionally.\n"
                        "Example: John Smith or Jane Doe"
                    )
                    st.session_state.context["conversation"].append({"role": "bot", "text": help_text})
                    handled = True

                # if message looks like tech stack
                elif "," in text and any(c.isalpha() for c in text):
                    # interpret as tech stack submission
                    techs = [t.strip() for t in re.split(r",|;", text) if t.strip()]
                    st.session_state.context["tech_stack"] = techs
                    st.session_state.context["conversation"].append({"role": "bot", "text": f"Tech stack recorded: {', '.join(techs)}"})
                    handled = True

                # if user asks to generate questions
                elif "generate" in text.lower() and st.session_state.context.get("tech_stack"):
                    per = 4
                    # Use fast generation by default for chat commands
                    use_ai = "ai" in text.lower() or "smart" in text.lower()
                    results = generate_questions_for_stack(st.session_state.context.get("tech_stack"), per, st.session_state.context.get("years_exp", ""), use_ai=use_ai)
                    st.session_state.last_generated = results
                    generation_type = "AI-powered" if use_ai else "fast local"
                    st.session_state.context["conversation"].append({"role": "bot", "text": f"Generated technical questions using {generation_type} generator."})
                    handled = True

                # fallback if nothing matched
                if not handled:
                    st.session_state.context["conversation"].append({"role": "bot", "text": FALLBACK_MESSAGE})
                
                st.rerun()


if __name__ == "__main__":
    main()


# -----------------------------
# README (also stored here for convenience)
# -----------------------------

README_MD = """
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
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
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
"""

# README content stored as string for reference
# (No longer auto-generating separate file - using main README.md instead)
