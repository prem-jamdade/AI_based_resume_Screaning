⭐ Talent Bridge – AI-Based ATS Resume Screening

Talent Bridge is an AI-powered ATS (Applicant Tracking System) built with Streamlit.
It analyzes resumes against a job description and generates an ATS score based on relevant skills, experience, education, and formatting.

🚀 Features

Upload resumes in PDF, DOCX, or TXT format

Automatic resume text extraction

NLP-based skill and keyword matching

Calculates:

Technical Skills Score

Experience Score

Education & Certifications Score

Soft Skills Score

Format Score

Clean circular ATS score visualization

MySQL-based data storage

Simple and modern UI

🛠️ Setup Instructions

Follow these steps to run this project on your system.

1️⃣ Clone the Repository
git clone <your-repo-link>
cd <project-folder>

2️⃣ Create a Virtual Environment

(Important: The venv folder is not included in GitHub, so you must create one locally.)

Windows
python -m venv venv
venv\Scripts\activate

Mac / Linux
python3 -m venv venv
source venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt


If you don’t have a requirements.txt yet, generate one using:

pip freeze > requirements.txt

4️⃣ MySQL Database Setup

Create a database:

CREATE DATABASE cv;


Create table:

CREATE TABLE resume_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_description TEXT,
    score FLOAT,
    timestamp DATETIME
);


Update your MySQL credentials inside App.py:

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='your_password',
    db='cv'
)

5️⃣ Run the Application
streamlit run App.py


The app will open in your browser:

http://localhost:8501

📝 Notes

Make sure your banner (banner.png) and logo (logo.webp) are inside the Logo folder.

NLTK data will download automatically on first run.

If you face path issues, verify file locations.
