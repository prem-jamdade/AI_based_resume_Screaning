import streamlit as st
import pandas as pd
import base64, random, time, datetime, io
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
from courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import pafy
import plotly.express as px
import nltk
import pyodbc

nltk.download('stopwords')


# -------------------- SQL SERVER CONNECTION -------------------- #
server = 'localhost'            
database = 'cv'                 
username = 'PRINCE_WORLD\9184'      
password = ''      

try:
    connection = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    cursor = connection.cursor()
    print("✅ Connected to SQL Server successfully!")
except Exception as e:
    st.error(f"❌ Error connecting to SQL Server: {e}")
    st.stop()


# Create table if not exists
table_sql = """
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='user_data' AND xtype='U')
CREATE TABLE user_data (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Name VARCHAR(500) NOT NULL,
    Email_ID VARCHAR(500) NOT NULL,
    resume_score VARCHAR(8) NOT NULL,
    Timestamp VARCHAR(50) NOT NULL,
    Page_no VARCHAR(5) NOT NULL,
    Predicted_Field NVARCHAR(MAX) NOT NULL,
    User_level NVARCHAR(MAX) NOT NULL,
    Actual_skills NVARCHAR(MAX) NOT NULL,
    Recommended_skills NVARCHAR(MAX) NOT NULL,
    Recommended_courses NVARCHAR(MAX) NOT NULL
);
"""
cursor.execute(table_sql)
connection.commit()


# -------------------- HELPER FUNCTIONS -------------------- #
def fetch_yt_video(link):
    video = pafy.new(link)
    return video.title


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    insert_sql = """
        INSERT INTO user_data (Name, Email_ID, resume_score, Timestamp, Page_no, Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_sql, (name, email, str(res_score), timestamp, str(no_of_pages), reco_field,
                                cand_level, skills, recommended_skills, courses))
    connection.commit()


# -------------------- STREAMLIT APP -------------------- #
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon='./Logo/logo2.png',
)


def run():
    img = Image.open('./Logo/logo2.png')
    st.image(img)
    st.title("AI Resume Analyzer")
    st.markdown('''<h5 style='text-align: left; color: #021659;'>Upload your resume and get smart recommendations</h5>''',
                unsafe_allow_html=True)

    pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])

    if pdf_file is not None:
        with st.spinner('Uploading your Resume...'):
            time.sleep(3)

        save_image_path = './Uploaded_Resumes/' + pdf_file.name
        with open(save_image_path, "wb") as f:
            f.write(pdf_file.getbuffer())

        show_pdf(save_image_path)
        resume_data = ResumeParser(save_image_path).get_extracted_data()

        if resume_data:
            resume_text = pdf_reader(save_image_path)

            st.header("**Resume Analysis**")
            st.success("Hello " + resume_data['name'])
            st.subheader("**Your Basic Info**")

            try:
                st.text('Name: ' + resume_data['name'])
                st.text('Email: ' + resume_data['email'])
                st.text('Contact: ' + resume_data['mobile_number'])
                st.text('Resume pages: ' + str(resume_data['no_of_pages']))
            except:
                pass

            cand_level = ''
            if resume_data['no_of_pages'] == 1:
                cand_level = "Fresher"
                st.markdown("<h4 style='color:#d73b5c;'>You are at Fresher level!</h4>", unsafe_allow_html=True)
            elif resume_data['no_of_pages'] == 2:
                cand_level = "Intermediate"
                st.markdown("<h4 style='color:#1ed760;'>You are at Intermediate level!</h4>", unsafe_allow_html=True)
            else:
                cand_level = "Experienced"
                st.markdown("<h4 style='color:#fba171;'>You are at Experienced level!</h4>", unsafe_allow_html=True)

            keywords = st_tags(label='### Your Current Skills',
                               text='See our skills recommendation below',
                               value=resume_data['skills'], key='1')

            # Keywords
            ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
            web_keyword = ['react', 'django', 'node js', 'php', 'laravel', 'javascript']
            android_keyword = ['android', 'flutter', 'kotlin', 'xml']
            ios_keyword = ['ios', 'swift', 'xcode']
            uiux_keyword = ['ux', 'figma', 'photoshop', 'illustrator', 'ui']

            recommended_skills = []
            reco_field = ''
            rec_course = ''

            for i in resume_data['skills']:
                if i.lower() in ds_keyword:
                    reco_field = 'Data Science'
                    st.success("**Our analysis says you are looking for Data Science Jobs.**")
                    recommended_skills = ['Data Visualization', 'ML Algorithms', 'Pytorch', 'Tensorflow', 'Flask', 'Streamlit']
                    st_tags(label='### Recommended Skills:', value=recommended_skills, key='2')
                    rec_course = course_recommender(ds_course)
                    break
                elif i.lower() in web_keyword:
                    reco_field = 'Web Development'
                    st.success("**Our analysis says you are looking for Web Development Jobs.**")
                    recommended_skills = ['React', 'Django', 'NodeJS', 'JavaScript', 'Flask']
                    st_tags(label='### Recommended Skills:', value=recommended_skills, key='3')
                    rec_course = course_recommender(web_course)
                    break
                elif i.lower() in android_keyword:
                    reco_field = 'Android Development'
                    st.success("**Our analysis says you are looking for Android App Development Jobs.**")
                    recommended_skills = ['Flutter', 'Kotlin', 'Java', 'SQLite']
                    st_tags(label='### Recommended Skills:', value=recommended_skills, key='4')
                    rec_course = course_recommender(android_course)
                    break
                elif i.lower() in ios_keyword:
                    reco_field = 'iOS Development'
                    st.success("**Our analysis says you are looking for iOS App Development Jobs.**")
                    recommended_skills = ['Swift', 'Xcode', 'Objective-C']
                    st_tags(label='### Recommended Skills:', value=recommended_skills, key='5')
                    rec_course = course_recommender(ios_course)
                    break
                elif i.lower() in uiux_keyword:
                    reco_field = 'UI/UX Design'
                    st.success("**Our analysis says you are looking for UI/UX Design Jobs.**")
                    recommended_skills = ['Figma', 'Wireframing', 'Prototyping', 'Adobe XD']
                    st_tags(label='### Recommended Skills:', value=recommended_skills, key='6')
                    rec_course = course_recommender(uiux_course)
                    break

            # Resume score
            ts = time.time()
            timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')

            st.subheader("**Resume Tips & Ideas💡**")
            resume_score = 0
            for section in ['Objective', 'Declaration', 'Hobbies', 'Achievements', 'Projects']:
                if section.lower() in resume_text.lower():
                    resume_score += 20
                    st.markdown(f"<h5 style='color:#1ed760;'>[+] Awesome! You added {section} section.</h5>",
                                unsafe_allow_html=True)
                else:
                    st.markdown(f"<h5 style='color:#000000;'>[-] Please add {section} section.</h5>",
                                unsafe_allow_html=True)

            st.subheader("**Resume Score📝**")
            my_bar = st.progress(0)
            for percent_complete in range(resume_score):
                time.sleep(0.05)
                my_bar.progress(percent_complete + 1)
            st.success(f"**Your Resume Score: {resume_score} / 100**")
            st.balloons()

            insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                        str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                        str(recommended_skills), str(rec_course))

            # Resume and interview videos
            st.header("**Bonus Video for Resume Writing Tips💡**")
            resume_vid = random.choice(resume_videos)
            st.subheader("✅ " + fetch_yt_video(resume_vid))
            st.video(resume_vid)

            st.header("**Bonus Video for Interview Tips💡**")
            interview_vid = random.choice(interview_videos)
            st.subheader("✅ " + fetch_yt_video(interview_vid))
            st.video(interview_vid)

        else:
            st.error('Something went wrong parsing your resume.')


run()
