import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Science Club Portal", page_icon="⚡", layout="wide")

if "users" not in st.session_state:
    st.session_state.users = pd.DataFrame(columns=["Name", "Email", "Department", "Designation", "Status"])

if "exams" not in st.session_state:
    st.session_state.exams = pd.DataFrame(columns=["Name", "Exam_Type", "Exam_Date", "Unavailable_From"])

st.sidebar.title("⚡ Science Club Portal")
menu = st.sidebar.selectbox("Navigation", ["Registration", "Availability Tracker"])

if menu == "Registration":
    st.header("📝 Member Registration")
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    dept = st.text_input("Department")
    designation = st.selectbox("Designation", ["Member", "Executive", "President"])
    if st.button("Register"):
        new_user = pd.DataFrame([[name, email, dept, designation, "Pending"]], columns=st.session_state.users.columns)
        st.session_state.users = pd.concat([st.session_state.users, new_user], ignore_index=True)
        st.success("Registration Successful!")

elif menu == "Availability Tracker":
    st.header("📅 Exam & Availability")
    if not st.session_state.users.empty:
        name = st.selectbox("Select Name", st.session_state.users["Name"].tolist())
        exam_type = st.selectbox("Exam Type", ["CT", "Semester Final"])
        exam_date = st.date_input("Exam Date")
        if st.button("Submit Exam"):
            unavailable_from = exam_date - timedelta(days=2 if exam_type == "CT" else 20)
            new_exam = pd.DataFrame([[name, exam_type, exam_date, unavailable_from]], columns=st.session_state.exams.columns)
            st.session_state.exams = pd.concat([st.session_state.exams, new_exam], ignore_index=True)
            st.success("Saved!")
        st.dataframe(st.session_state.exams)
    else:
        st.warning("Register a user first!")
