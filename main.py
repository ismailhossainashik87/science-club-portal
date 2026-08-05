from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="Science Club Portal", page_icon="⚡", layout="wide")

# Database Initialization
if "users" not in st.session_state:
    st.session_state.users = pd.DataFrame(columns=["Name", "Email", "Department", "Designation", "Status"])

if "exams" not in st.session_state:
    st.session_state.exams = pd.DataFrame(columns=["Name", "Exam_Type", "Exam_Date", "Unavailable_From", "Justification"])

if "work_logs" not in st.session_state:
    st.session_state.work_logs = pd.DataFrame(columns=["Name", "Date", "Hours", "Core_Work", "Assigned_By"])

# Sidebar Navigation
st.sidebar.title("⚡ Science Club Portal")
menu = st.sidebar.selectbox(
    "Navigation",
    ["Registration", "Exam & Availability", "Work Log & Contribution", "Admin Dashboard"]
)

# 1. REGISTRATION
if menu == "Registration":
    st.header("📝 Member Registration")
    with st.form("reg_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        dept = st.text_input("Department")
        designation = st.selectbox("Club Designation", ["Member", "Executive", "Joint Secretary", "Secretary", "President"])
        submit = st.form_submit_button("Register")

        if submit:
            if name and email:
                new_user = pd.DataFrame([[name, email, dept, designation, "Pending"]], columns=st.session_state.users.columns)
                st.session_state.users = pd.concat([st.session_state.users, new_user], ignore_index=True)
                st.success("Registration successful! Waiting for Admin Approval.")
            else:
                st.error("Please fill up all required fields.")

# 2. EXAM & AVAILABILITY
elif menu == "Exam & Availability":
    st.header("📅 Exam Date & Availability Tracker")
    approved_users = st.session_state.users[st.session_state.users["Status"] == "Approved"]["Name"].tolist()

    if not approved_users:
        st.warning("No approved members found. Admin needs to approve first.")
    else:
        with st.form("exam_form"):
            name = st.selectbox("Select Your Name", approved_users)
            exam_type = st.selectbox("Exam Type", ["Class Test (CT)", "Semester Final", "Yearly Exam"])
            exam_date = st.date_input("Exam Date")
            justification = st.text_area("Late Notice Justification:")
            exam_submit = st.form_submit_button("Submit Exam Schedule")

            if exam_submit:
                if exam_type == "Class Test (CT)":
                    unavailable_from = exam_date - timedelta(days=2)
                elif exam_type == "Semester Final":
                    unavailable_from = exam_date - timedelta(days=20)
                else:
                    unavailable_from = exam_date - timedelta(days=30)

                new_exam = pd.DataFrame([[name, exam_type, exam_date, unavailable_from, justification]], columns=st.session_state.exams.columns)
                st.session_state.exams = pd.concat([st.session_state.exams, new_exam], ignore_index=True)
                st.success("Exam schedule updated successfully!")
        
        st.subheader("Live Availability Status")
        if not st.session_state.exams.empty:
            df = st.session_state.exams.copy()
            today = datetime.now().date()
            status_list = []
            for idx, row in df.iterrows():
                u_date = pd.to_datetime(row["Unavailable_From"]).date()
                e_date = pd.to_datetime(row["Exam_Date"]).date()
                if u_date <= today <= e_date:
                    status_list.append("🔴 Unavailable")
                else:
                    status_list.append("🟢 Available")
            df["Live_Status"] = status_list
            st.dataframe(df)

# 3. WORK LOG
elif menu == "Work Log & Contribution":
    st.header("💼 Daily Work Tracker")
    approved_users = st.session_state.users[st.session_state.users["Status"] == "Approved"]["Name"].tolist()

    if not approved_users:
        st.warning("Please get approved by admin first.")
    else:
        with st.form("work_form"):
            name = st.selectbox("Select Member Name", approved_users)
            date = st.date_input("Work Date")
            hours = st.number_input("Time Spent (Hours)", min_value=0.5, step=0.5)
            core_work = st.text_area("Work Description")
            assigned_by = st.text_input("Assigned By")
            work_submit = st.form_submit_button("Submit Work Log")

            if work_submit:
                new_log = pd.DataFrame([[name, date, hours, core_work, assigned_by]], columns=st.session_state.work_logs.columns)
                st.session_state.work_logs = pd.concat([st.session_state.work_logs, new_log], ignore_index=True)
                st.success("Work log saved successfully!")

# 4. ADMIN DASHBOARD
elif menu == "Admin Dashboard":
    st.header("⚙️ Admin Panel")
    tab1, tab2, tab3 = st.tabs(["Member Approvals", "Master Exam View", "Monthly Assessment"])

    with tab1:
        st.subheader("Pending Registrations")
        pending_df = st.session_state.users[st.session_state.users["Status"] == "Pending"]
        if not pending_df.empty:
            for idx, row in pending_df.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{row['Name']}** ({row['Department']}) - {row['Designation']}")
                if col2.button("Approve", key=f"app_{idx}"):
                    st.session_state.users.loc[idx, "Status"] = "Approved"
                    st.rerun()
        else:
            st.info("No pending requests.")

    with tab2:
        st.subheader("Exam & Availability Data")
        if not st.session_state.exams.empty:
            st.dataframe(st.session_state.exams)
            csv = st.session_state.exams.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "exams.csv", "text/csv")
        else:
            st.info("No exam data yet.")

    with tab3:
        st.subheader("Performance Evaluation")
        if not st.session_state.work_logs.empty:
            summary = st.session_state.work_logs.groupby("Name").agg({"Hours": "sum", "Core_Work": "count"}).reset_index()
            summary.columns = ["Name", "Total_Hours_Spent", "Total_Tasks_Done"]
            st.dataframe(summary)
        else:
            st.info("No work logs submitted yet.")
