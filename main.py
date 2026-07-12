import streamlit as st
import PyPDF2
import io
import os
import json
import re
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Critiquer",
    page_icon="📃",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# COLOR PALETTE
# ----------------------------------------------------------------------
DARK_PLUM   = "#312C51"   # deep background / headings
GOLD_PEACH  = "#F0C38E"   # accents / buttons
CORAL_PINK  = "#F1AA9B"   # highlights / hover
SOFT_VIOLET = "#48426D"   # cards / secondary background

# ----------------------------------------------------------------------
# FREE MODELS (OpenRouter) — tried in order, first that succeeds wins
# ----------------------------------------------------------------------
FREE_MODELS = [
    "openrouter/free",                        # auto-router: picks a working free model for you
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-20b:free",
]

# ----------------------------------------------------------------------
# CUSTOM CSS
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{
            background: linear-gradient(160deg, {DARK_PLUM} 0%, {SOFT_VIOLET} 55%, {DARK_PLUM} 100%);
            color: #F5F1EE;
        }}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        .hero-container {{
            text-align: center;
            padding: 2rem 1rem 1.5rem 1rem;
        }}
        .hero-title {{
            font-size: 2.6rem;
            font-weight: 800;
            color: {GOLD_PEACH};
            margin-bottom: 0.2rem;
            letter-spacing: -0.5px;
        }}
        .hero-subtitle {{
            font-size: 1.05rem;
            color: #E8E1F5;
            font-weight: 400;
            opacity: 0.9;
        }}

        .glass-card {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(240, 195, 142, 0.25);
            border-radius: 18px;
            padding: 1.8rem 1.6rem;
            margin-bottom: 1.4rem;
            backdrop-filter: blur(6px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        }}

        .section-label {{
            color: {GOLD_PEACH};
            font-weight: 700;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.6rem;
        }}

        [data-testid="stFileUploader"] {{
            background: rgba(255,255,255,0.04);
            border: 1.5px dashed {CORAL_PINK};
            border-radius: 14px;
            padding: 0.8rem;
        }}
        [data-testid="stFileUploaderDropzoneInstructions"] span {{
            color: #F5F1EE !important;
        }}

        .stTextInput > div > div > input,
        .stSelectbox > div > div {{
            background-color: rgba(255,255,255,0.08);
            color: #F5F1EE;
            border: 1px solid {SOFT_VIOLET};
            border-radius: 10px;
        }}
        .stTextInput label, .stSelectbox label {{
            color: {GOLD_PEACH} !important;
            font-weight: 600;
        }}

        .stButton > button {{
            background: linear-gradient(90deg, {CORAL_PINK} 0%, {GOLD_PEACH} 100%);
            color: {DARK_PLUM};
            font-weight: 700;
            border: none;
            border-radius: 12px;
            padding: 0.6rem 1.6rem;
            width: 100%;
            transition: all 0.25s ease;
            box-shadow: 0 4px 14px rgba(241, 170, 155, 0.35);
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(240, 195, 142, 0.45);
            color: {DARK_PLUM};
        }}

        .stDownloadButton > button {{
            background: transparent;
            color: {GOLD_PEACH};
            border: 1.5px solid {GOLD_PEACH};
            border-radius: 12px;
            font-weight: 600;
            width: 100%;
        }}
        .stDownloadButton > button:hover {{
            background: {GOLD_PEACH};
            color: {DARK_PLUM};
        }}

        .result-card {{
            background: rgba(255, 255, 255, 0.07);
            border-left: 5px solid {GOLD_PEACH};
            border-radius: 14px;
            padding: 1.6rem;
            color: #F5F1EE;
            line-height: 1.65;
        }}

        .score-hero {{
            text-align: center;
            padding: 1.4rem 1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(240,195,142,0.3);
            margin-bottom: 1.2rem;
        }}
        .score-number {{
            font-size: 3.4rem;
            font-weight: 800;
            color: {GOLD_PEACH};
            line-height: 1;
        }}
        .score-label {{
            font-size: 1rem;
            color: {CORAL_PINK};
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 0.3rem;
        }}

        .pill {{
            display: inline-block;
            padding: 0.3rem 0.85rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0.2rem 0.3rem 0.2rem 0;
        }}
        .pill-found {{
            background: rgba(240,195,142,0.2);
            color: {GOLD_PEACH};
            border: 1px solid {GOLD_PEACH};
        }}
        .pill-missing {{
            background: rgba(241,170,155,0.15);
            color: {CORAL_PINK};
            border: 1px solid {CORAL_PINK};
        }}

        .strength-item, .weakness-item {{
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}

        section[data-testid="stSidebar"] {{
            background: {DARK_PLUM};
            border-right: 1px solid {SOFT_VIOLET};
        }}
        section[data-testid="stSidebar"] * {{
            color: #F5F1EE !important;
        }}
        section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{
            color: {GOLD_PEACH} !important;
        }}

        [data-testid="stMetricValue"] {{
            color: {GOLD_PEACH} !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: #E8E1F5 !important;
        }}

        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, {CORAL_PINK}, {GOLD_PEACH});
        }}

        .footer-credit {{
            text-align: center;
            margin-top: 2.5rem;
            padding: 1rem;
            color: {CORAL_PINK};
            font-size: 0.9rem;
            opacity: 0.85;
            border-top: 1px solid rgba(240,195,142,0.2);
        }}
        .footer-credit b {{
            color: {GOLD_PEACH};
        }}

        .stAlert {{
            border-radius: 12px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------
if "analyses_run" not in st.session_state:
    st.session_state.analyses_run = 0

# ----------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">📃 AI Resume Critiquer</div>
        <div class="hero-subtitle">Upload your resume and get instant, AI-powered feedback tailored to the role you want</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ✨ How it works")
    st.markdown(
        """
        1. **Upload** your resume (PDF or TXT)
        2. **Add** the job role you're targeting (optional but recommended)
        3. Hit **Analyze Resume**
        4. Get a score, ATS keyword check, and structured feedback
        """
    )
    st.markdown("---")

    st.markdown("## ⚙️ Settings")
    model_choice = st.selectbox(
        "AI model",
        FREE_MODELS,
        index=0,
        help="All options are free OpenRouter models. If one is rate-limited, the app automatically falls back to the next.",
    )

    manual_key = st.text_input(
        "OpenRouter API key (optional override)",
        type="password",
        help="Only needed if you haven't set OPENROUTER_API_KEY in a .env file.",
        placeholder="sk-or-...",
    )

    st.markdown("---")
    st.markdown("## 💡 Tips for a strong resume")
    st.markdown(
        """
        - Lead bullet points with action verbs
        - Quantify impact wherever possible
        - Keep it to 1 page for internships
        - Tailor keywords to the job description
        """
    )
    st.markdown("---")
    st.metric("Analyses this session", st.session_state.analyses_run)
    st.caption("Made with 💜 by **Ameema Azeem**")

# ----------------------------------------------------------------------
# API KEY
# ----------------------------------------------------------------------
OPENROUTER_API_KEY = manual_key.strip() if manual_key else os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.warning(
        "⚠️ No OpenRouter API key found. Get a free key at "
        "[openrouter.ai/keys](https://openrouter.ai/keys) and add it to a `.env` file as "
        "`OPENROUTER_API_KEY=sk-or-...`, or paste it in the sidebar."
    )

# ----------------------------------------------------------------------
# MAIN INPUT CARD
# ----------------------------------------------------------------------
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

st.markdown('<div class="section-label">📤 Upload Resume</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload your resume (PDF or TXT)",
    type=["pdf", "txt"],
    label_visibility="collapsed",
)

st.markdown('<div class="section-label" style="margin-top:1.2rem;">🎯 Target Role</div>', unsafe_allow_html=True)
job_role = st.text_input(
    "Enter the job role you're targeting (optional)",
    placeholder="e.g. Marketing Intern, Data Analyst, Software Engineer...",
    label_visibility="collapsed",
)

if uploaded_file:
    st.caption(f"📎 {uploaded_file.name} ready")

st.markdown("<br>", unsafe_allow_html=True)
analyze = st.button("🚀 Analyze Resume")

st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")


def word_count(text):
    return len(text.split())


def estimated_read_time(word_count_value):
    minutes = max(1, round(word_count_value / 200))
    return minutes


def build_prompt(file_content, job_role):
    role_text = job_role if job_role else "general job applications"
    return f"""You are an expert resume reviewer with years of experience in HR and recruitment.
Analyze the resume below for a candidate targeting: {role_text}.

Respond with ONLY a valid JSON object (no markdown fences, no commentary) with this exact structure:
{{
  "overall_score": <integer 0-100>,
  "category_scores": {{
    "content_clarity": <integer 0-100>,
    "skills_presentation": <integer 0-100>,
    "experience_impact": <integer 0-100>,
    "ats_compatibility": <integer 0-100>
  }},
  "strengths": ["<3 to 5 short strengths>"],
  "weaknesses": ["<3 to 5 short weaknesses>"],
  "recommendations": ["<5 to 7 specific, actionable improvements>"],
  "missing_keywords": ["<important keywords/skills for the target role that are missing from the resume, empty list if role not specified or none missing>"],
  "found_keywords": ["<important keywords/skills for the target role that ARE present in the resume, empty list if role not specified>"]
}}

Resume content:
{file_content}
"""


def call_openrouter(api_key, models, prompt):
    """Try each free model in order until one returns a usable response."""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    last_error = None
    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume reviewer. Always respond with valid JSON only, no extra text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=1400,
                extra_headers={
                    "HTTP-Referer": "https://streamlit.io",
                    "X-Title": "AI Resume Critiquer",
                },
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content, model
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All free models failed. Last error: {last_error}")


def parse_ai_json(raw_text):
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def score_label(score):
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 50:
        return "Needs Work"
    return "Needs Major Revision"


# ----------------------------------------------------------------------
# PRE-ANALYSIS SNAPSHOT (word count / read time once a file is uploaded)
# ----------------------------------------------------------------------
if uploaded_file and not analyze:
    try:
        preview_bytes = uploaded_file.getvalue()
        if uploaded_file.type == "application/pdf":
            preview_text = extract_text_from_pdf(io.BytesIO(preview_bytes))
        else:
            preview_text = preview_bytes.decode("utf-8", errors="ignore")
        wc = word_count(preview_text)
        c1, c2 = st.columns(2)
        c1.metric("Word count", wc)
        c2.metric("Est. read time", f"{estimated_read_time(wc)} min")
    except Exception:
        pass

# ----------------------------------------------------------------------
# ANALYSIS LOGIC
# ----------------------------------------------------------------------
if analyze:
    if not uploaded_file:
        st.error("📎 Please upload a resume file first.")
    elif not OPENROUTER_API_KEY:
        st.error("🔑 Missing OpenRouter API key. Add it in the sidebar or your `.env` file.")
    else:
        try:
            with st.spinner("Reading your resume..."):
                file_content = extract_text_from_file(uploaded_file)

            if not file_content.strip():
                st.error("The uploaded file doesn't contain any readable text.")
                st.stop()

            prompt = build_prompt(file_content, job_role)

            models_to_try = [model_choice] + [m for m in FREE_MODELS if m != model_choice]

            with st.spinner("Analyzing your resume... this usually takes a few seconds ✨"):
                raw_text, used_model = call_openrouter(OPENROUTER_API_KEY, models_to_try, prompt)

            st.session_state.analyses_run += 1

            try:
                data = parse_ai_json(raw_text)
            except (json.JSONDecodeError, ValueError):
                data = None

            if data:
                overall = int(data.get("overall_score", 0))
                cats = data.get("category_scores", {})
                strengths = data.get("strengths", [])
                weaknesses = data.get("weaknesses", [])
                recommendations = data.get("recommendations", [])
                missing_kw = data.get("missing_keywords", [])
                found_kw = data.get("found_keywords", [])

                st.markdown(
                    f"""
                    <div class="score-hero">
                        <div class="score-number">{overall}/100</div>
                        <div class="score-label">{score_label(overall)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="section-label">📊 Category Breakdown</div>', unsafe_allow_html=True)
                label_map = {
                    "content_clarity": "Content Clarity",
                    "skills_presentation": "Skills Presentation",
                    "experience_impact": "Experience Impact",
                    "ats_compatibility": "ATS Compatibility",
                }
                for key, label in label_map.items():
                    val = int(cats.get(key, 0))
                    st.markdown(f"**{label}** — {val}/100")
                    st.progress(min(max(val, 0), 100) / 100)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="section-label">✅ Strengths</div>', unsafe_allow_html=True)
                    for s in strengths:
                        st.markdown(f'<div class="strength-item">✔️ {s}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="section-label">⚠️ Areas to Improve</div>', unsafe_allow_html=True)
                    for w in weaknesses:
                        st.markdown(f'<div class="weakness-item">➖ {w}</div>', unsafe_allow_html=True)

                if job_role and (found_kw or missing_kw):
                    st.markdown('<div class="section-label" style="margin-top:1.2rem;">🔑 ATS Keyword Match</div>', unsafe_allow_html=True)
                    kw_html = ""
                    for kw in found_kw:
                        kw_html += f'<span class="pill pill-found">✓ {kw}</span>'
                    for kw in missing_kw:
                        kw_html += f'<span class="pill pill-missing">✗ {kw}</span>'
                    st.markdown(kw_html, unsafe_allow_html=True)

                st.markdown('<div class="section-label" style="margin-top:1.2rem;">🛠️ Recommendations</div>', unsafe_allow_html=True)
                rec_html = "<div class='result-card'><ol>"
                for r in recommendations:
                    rec_html += f"<li style='margin-bottom:0.5rem;'>{r}</li>"
                rec_html += "</ol></div>"
                st.markdown(rec_html, unsafe_allow_html=True)

                report_lines = [
                    "AI Resume Critique Report",
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    f"Target Role: {job_role or 'General'}",
                    f"Model used: {used_model}",
                    "",
                    f"OVERALL SCORE: {overall}/100 ({score_label(overall)})",
                    "",
                    "CATEGORY SCORES:",
                ]
                for key, label in label_map.items():
                    report_lines.append(f"  - {label}: {cats.get(key, 'N/A')}/100")
                report_lines += ["", "STRENGTHS:"]
                report_lines += [f"  - {s}" for s in strengths]
                report_lines += ["", "AREAS TO IMPROVE:"]
                report_lines += [f"  - {w}" for w in weaknesses]
                if job_role:
                    report_lines += ["", "FOUND KEYWORDS:", ", ".join(found_kw) or "None"]
                    report_lines += ["", "MISSING KEYWORDS:", ", ".join(missing_kw) or "None"]
                report_lines += ["", "RECOMMENDATIONS:"]
                report_lines += [f"  {i+1}. {r}" for i, r in enumerate(recommendations)]
                report = "\n".join(report_lines)

            else:
                # Fallback: model didn't return valid JSON, show raw text
                st.markdown('<div class="section-label">📊 Analysis Results</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="result-card">{raw_text}</div>', unsafe_allow_html=True)
                report = (
                    f"AI Resume Critique Report\n"
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    f"Target Role: {job_role or 'General'}\n"
                    f"Model used: {used_model}\n\n{raw_text}"
                )

            st.download_button(
                label="⬇️ Download Feedback as TXT",
                data=report,
                file_name="resume_feedback.txt",
                mime="text/plain",
            )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown(
    """
    <div class="footer-credit">
        Built with <b>Streamlit</b> &amp; <b>OpenRouter</b> · Designed &amp; developed by <b>Ameema Azeem</b>
    </div>
    """,
    unsafe_allow_html=True,
)