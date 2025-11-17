import streamlit as st
from io import BytesIO
import re
import os
from datetime import datetime
from collections import Counter
import math
import base64
import time
import pymysql

# For PDF and DOCX parsing
import PyPDF2
import docx

# NLP
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from difflib import get_close_matches

# Visualization
import matplotlib.pyplot as plt
import pandas as pd

# Ensure NLTK data
nltk_packages = ["punkt", "stopwords", "wordnet", "omw-1.4"]
for pkg in nltk_packages:
    try:
        nltk.data.find(pkg)
    except Exception:
        nltk.download(pkg)

nltk.download('punkt_tab')

STOPWORDS = set(stopwords.words('english'))
LEMMATIZER = WordNetLemmatizer()

# ----------------------- DATABASE CONNECTION -----------------------
try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='cse#654321',
        db='cv'
    )
    cursor = connection.cursor()
except Exception as e:
    st.warning(f"⚠️ Database connection failed: {e}")

# ----------------------- SKILLS DATABASE -----------------------
SKILLS_DB = {
    'python','java','c++','c','c#','javascript','typescript','react','angular','vue',
    'node.js','django','flask','spring','spring boot','sql','mysql','postgresql',
    'mongodb','redis','docker','kubernetes','aws','azure','gcp','tensorflow','pytorch',
    'pandas','numpy','spark','hadoop','tableau','power bi','excel','machine learning'
}
DEGREE_KEYWORDS = ['b.tech','b.e','bachelors','bachelor','m.tech','m.e','masters','ms','phd']
CERT_KEYWORDS = ['aws','azure','google cloud','gcp','sql','tableau','power bi']
SOFT_SKILLS = ['communication','team','leadership','collaborate','problem solving','analytical']

# ----------------------- HELPERS -----------------------
def clean_text(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-/.@]", ' ', text)
    tokens = nltk.word_tokenize(text)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    tokens = [LEMMATIZER.lemmatize(t) for t in tokens]
    return tokens

def extract_text_from_pdf(file_bytes: bytes):
    reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or '')
    return '\n'.join(text)

def extract_text_from_docx(file_bytes: bytes):
    with BytesIO(file_bytes) as f:
        doc = docx.Document(f)
        paragraphs = [p.text for p in doc.paragraphs]
    return '\n'.join(paragraphs)

def extract_text(uploaded_file):
    if uploaded_file is None:
        return ''
    raw = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith('.pdf'):
        return extract_text_from_pdf(raw)
    elif name.endswith('.docx'):
        return extract_text_from_docx(raw)
    else:
        return raw.decode('utf-8', errors='ignore')

def extract_years_of_experience(text):
    matches = re.findall(r"(\d{1,2})\+?\s+years", text.lower())
    if matches:
        try:
            return max([int(m) for m in matches])
        except:
            return 0
    return 0

# ----------------------- MAIN SCORING -----------------------
def score_resume_against_jd(resume_text, jd_text):
    resume_tokens = clean_text(resume_text)
    jd_tokens = clean_text(jd_text)

    jd_skills = [w for w in jd_tokens if w in SKILLS_DB]
    matched_skills = [s for s in jd_skills if s in resume_tokens]
    skill_score = (len(matched_skills) / max(1, len(jd_skills))) * 40

    years = extract_years_of_experience(resume_text)
    exp_score = min(25, (years / 10) * 25)

    edu_flag = any(d in resume_text.lower() for d in DEGREE_KEYWORDS)
    certs = [c for c in CERT_KEYWORDS if c in resume_text.lower()]
    edu_score = 10 if edu_flag else 5
    cert_score = min(5, len(certs))
    education_score = edu_score + cert_score

    soft_found = [s for s in SOFT_SKILLS if s in resume_text.lower()]
    soft_score = (len(soft_found) / len(SOFT_SKILLS)) * 10

    format_score = 10 if any(h in resume_text.lower() for h in ['skills','projects','experience','education']) else 6

    total = round(skill_score + exp_score + education_score + soft_score + format_score, 2)

    return {
        'technical': round(skill_score,2),
        'experience': round(exp_score,2),
        'education': round(education_score,2),
        'soft': round(soft_score,2),
        'format': round(format_score,2),
        'total': total
    }

# ----------------------- STREAMLIT UI -----------------------
st.set_page_config(page_title="Talent Bridge - Resume Screaning", page_icon='./Logo/logo.webp', layout='wide')

st.markdown("""
<style>
.header {
  background: linear-gradient(90deg,#0f172a,#0ea5e9);
  padding: 18px;
  border-radius: 12px;
  color: white;
}
</style>
""", unsafe_allow_html=True)

# ----------------------- STYLING -----------------------
st.markdown("""
    <style>
    .header {
        background: (90deg, rgba(255, 223, 128, 0.8), rgba(255, 187, 64, 0.9));
        padding: 10px;
        border-radius: 12px;
        color: #ECECEC;
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        font-size: 28px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
        margin-bottom: 15px;
    }

    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FFD700, #FFA500);
        color: #ECECEC;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.5em;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease-in-out;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }

    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #FFC300, #FF8C00);
        transform: scale(1.03);
        box-shadow: 0px 6px 12px rgba(0,0,0,0.25);
    }
    .ats-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 40px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">AI Based ATS Resume Screening</div>', unsafe_allow_html=True)

# ----------------------- BANNER IMAGE  -----------------------
banner_path = "./Logo/banner.png"

if os.path.exists(banner_path):
    with open(banner_path, "rb") as f:
        banner_bytes = f.read()
    banner_base64 = base64.b64encode(banner_bytes).decode()

    banner_html = f"""
        <style>
        .banner {{
            width: 100%;
            max-width: 100%;
            height: 150px;
            border-radius: 12px;
            margin-top: 10px;
            display: block;
            object-fit: contain;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        }}
        .banner-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin-bottom: 40px;
        }}
        </style>
        <div class="banner-container">
            <img class="banner" src="data:image/png;base64,{banner_base64}" alt="Talent Bridge Banner">
        </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)
else:
    st.warning("⚠️ Banner image not found. Please check your path.")


jd_text = st.text_area("🧾 Enter Job Description", height=180)
uploaded_file = st.file_uploader("📎 Upload Resume (PDF/DOCX/TXT)", type=['pdf','docx','txt'])

if st.button("Analyze Resume"):
    if not jd_text or not uploaded_file:
        st.error("Please provide both Job Description and Resume.")
    else:
        placeholder = st.empty()

        placeholder.info("Uploading and reading resume...")
        time.sleep(1)
        resume_text = extract_text(uploaded_file)
        placeholder.success("✅ Uploading and reading resume completed.")
        time.sleep(0.5)

        if not resume_text.strip():
            st.error("Couldn't extract text. Please upload a valid resume file.")
        else:
            placeholder.info("Analyzing resume content...")
            time.sleep(1.5)
            placeholder.success("✅ Analyzing resume content completed.")
            time.sleep(0.5)

            placeholder.info("Matching skills and job requirements...")
            time.sleep(1)
            placeholder.success("✅ Matching skills and job requirements completed.")
            time.sleep(0.5)

            result = score_resume_against_jd(resume_text, jd_text)
            score = int(result['total'])
            percentage = min(max(score, 0), 100)

            circumference = 2 * math.pi * 90
            dash_offset = circumference - (circumference * percentage / 100)

            # ----------------------- ATS SCORE CARD -----------------------
            st.markdown("<h3 style='text-align:center; margin-top:30px;'>ATS Score</h3>", unsafe_allow_html=True)

            if percentage < 50:
                color = "#e74c3c"   
                level = "Low"
            elif percentage < 75:
                color = "#f4b400"   
                level = "Average"
            else:
                color = "#2ecc71"   
                level = "Good"

            score_card_html = f"""
            <style>
            .score-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                margin-top: 20px;
            }}

            .score-card {{
                position: relative;
                width: 220px;
                height: 220px;
            }}

            .score-svg {{
                transform: rotate(-90deg);
                width: 220px;
                height: 220px;
            }}

            .score-circle-bg {{
                fill: none;
                stroke: #e6e6e6;
                stroke-width: 15;
            }}

            .score-circle {{
                fill: none;
                stroke: {color};
                stroke-width: 15;
                stroke-linecap: round;
                stroke-dasharray: {circumference};
                stroke-dashoffset: {dash_offset};
                transition: stroke-dashoffset 1.2s ease-in-out;
            }}

            .score-value {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 56px;
                font-weight: 700;
                color: #1a1a1a;
                font-family: 'Segoe UI', sans-serif;
            }}

            .score-label {{
                margin-top: 15px;
                font-size: 22px;
                font-weight: 600;
                color: {color};
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            </style>

            <div class="score-container">
                <div class="score-card">
                    <svg class="score-svg" viewBox="0 0 220 220" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                        <circle class="score-circle-bg" cx="110" cy="110" r="90" />
                        <circle class="score-circle" cx="110" cy="110" r="90" />
                    </svg>
                    <div class="score-value">{percentage}</div>
                </div>
                <div class="score-label">{level}</div>
            </div>
            """
            st.markdown(score_card_html, unsafe_allow_html=True)

            # ----------------------- SAVE TO MYSQL -----------------------
            try:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO resume_analysis (job_description, score, timestamp)
                    VALUES (%s, %s, %s)
                """, (jd_text[:500], result['total'], now))
                connection.commit()
            except Exception:
                pass

st.markdown("---")
st.caption("⚙️ AI Based ATS Resume Scoring @Talent Bridge")

