import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import smtplib
from email.mime.text import MIMEText
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# ---------------------------------------------------------
# SETUP & GOOGLE SHEETS CONNECTION
# ---------------------------------------------------------
st.set_page_config(page_title="Science Club Portal", page_icon="⚡", layout="wide")

def get_sheets_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        secret_dict = json.loads(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open("ScienceClubDB")

def load_data(sheet_name, expected_columns):
    try:
        sh = get_sheets_connection()
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        sh = get_sheets_connection()
        ws = sh.worksheet(sheet_name)
        ws.append_row(expected_columns)
        return pd.DataFrame(columns=expected_columns)

def update_sheet_data(sheet_name, df):
    sh = get_sheets_connection()
    ws = sh.worksheet(sheet_name)
    ws.clear()
    ws.append_row(list(df.columns))
    for _, row in df.iterrows():
        ws.append_row([str(val) for val in row])

def append_row_to_sheet(sheet_name, row_data):
    sh = get_sheets_connection()
    ws = sh.worksheet(sheet_name)
    ws.append_row([str(val) for val in row_data])

# Define Column Structures
user_cols = ["ID", "Name", "Email", "Department", "Designation", "Gender", "DOB", "Status"]
exam_cols = ["ID", "Name", "Exam_Type", "Exam_Date", "Unavailable_From", "Justification"]
work_cols = ["ID", "Name", "Date", "Start_Time", "End_Time", "Total_Hours", "Core_Work", "Extra_Dedication", "Why_Work", "Assigned_By"]
leave_cols = ["ID", "Name", "Reason", "Start_Datetime", "End_Datetime"]

# Load Data from Google Sheets into Session State
if "users" not in st.session_state:
    st.session_state.users = load_data("users", user_cols)
if "exams" not in st.session_state:
    st.session_state.exams = load_data("exams", exam_cols)
if "work_logs" not in st.session_state:
    st.session_state.work_logs = load_data("work_logs", work_cols)
if "leaves" not in st.session_state:
    st.session_state.leaves = load_data("leaves", leave_cols)

# Login State
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# Helper Functions
def generate_id():
    users_df = load_data("users", user_cols)
    return f"SC-{1001 + len(users_df)}"

def check_availability(user_id):
    today = datetime.now().date()
    now = datetime.now()
    
    # Reload leaves & exams from sheets for real-time check
    leaves_df = load_data("leaves", leave_cols)
    user_leaves = leaves_df[leaves_df["ID"] == user_id]
    for _, row in user_leaves.iterrows():
        try:
            s_dt = pd.to_datetime(row["Start_Datetime"])
            e_dt = pd.to_datetime(row["End_Datetime"])
            if s_dt <= now <= e_dt:
                return False, f"🔴 Unavailable (Leave: {row['Reason']})"
        except:
            pass
            
    exams_df = load_data("exams", exam_cols)
    user_exams = exams_df[exams_df["ID"] == user_id]
    for _, row in user_exams.iterrows():
        try:
            u_date = pd.to_datetime(row["Unavailable_From"]).date()
            e_date = pd.to_datetime(row["Exam_Date"]).date()
            if u_date <= today <= e_date:
                return False, f"🔴 Unavailable ({row['Exam_Type']} Exam)"
        except:
            pass
            
    return True, "🟢 Available"

def send_approval_email(to_email, user_name, member_id):
    sender_email = "ismailhossainashik87@gmail.com" 
    sender_password = "azardcvvawqzsvnl"

    subject = "Science Club - Account Approved!"
    body = f"Hello {user_name},\n\nCongratulations! Your registration for the Science Club has been approved.\n\nYour official Member ID is: {member_id}\n\nPlease use this ID to log in to our portal.\n\nBest Regards,\nScience Club Admin"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        return False

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("⚡ SC Portal")

if st.session_state.logged_in_user:
    st.sidebar.success(f"Logged in as: {st.session_state.logged_in_user['Name']}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()
    menu = st.sidebar.radio("Navigation", ["My Dashboard", "Admin Panel"])
else:
    menu = st.sidebar.radio("Navigation", ["Login / Register", "Admin Panel"])

# ---------------------------------------------------------
# 1. LOGIN & REGISTRATION
# ---------------------------------------------------------
if menu == "Login / Register":
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🔑 Member Login")
        login_id = st.text_input("Enter your Member ID (e.g., SC-1001)")
        if st.button("Login"):
            users_df = load_data("users", user_cols)
            user_match = users_df[(users_df["ID"] == login_id.strip()) & (users_df["Status"] == "Approved")]
            if not user_match.empty:
                st.session_state.logged_in_user = user_match.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Invalid ID or Account not approved yet!")

    with col2:
        st.header("📝 New Registration")
        with st.form("reg_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            dob = st.date_input("Date of Birth", min_value=date(1980, 1, 1), max_value=date.today())
            dept = st.text_input("Department")
            designation = st.text_input("Club Designation (e.g., Executive, Member)")
            
            submit = st.form_submit_button("Submit Registration")

            if submit:
                users_df = load_data("users", user_cols)
                if not name or not email or not dept or not designation:
                    st.error("Please fill all fields!")
                elif not users_df.empty and email in users_df["Email"].values:
                    st.error("❌ This email is used before. Try another one.")
                else:
                    new_id = generate_id()
                    new_row = [new_id, name, email, dept, designation, gender, str(dob), "Pending"]
                    append_row_to_sheet("users", new_row)
                    st.success("✅ Registration successful! Please wait for admin approval. You will receive your Member ID via email once approved.")

# ---------------------------------------------------------
# 2. USER DASHBOARD
# ---------------------------------------------------------
elif menu == "My Dashboard" and st.session_state.logged_in_user:
    user = st.session_state.logged_in_user
    st.header(f"Welcome, {user['Name']}! 👋")
    
    is_avail, avail_text = check_availability(user['ID'])
    st.info(f"**Current Status:** {avail_text}")

    tab1, tab2, tab3 = st.tabs(["📚 Exam Notice", "💼 Work Log", "🏃‍♂️ Sudden Leave"])
    
    # --- EXAM NOTICE ---
    with tab1:
        st.subheader("Submit Exam Schedule")
        exam_type = st.selectbox("Exam Type", ["Class Test (CT)", "Semester Final", "Yearly Exam"])
        exam_date = st.date_input("Exam Date")
        
        if exam_type == "Class Test (CT)":
            unavailable_from = exam_date - timedelta(days=2)
        elif exam_type == "Semester Final":
            unavailable_from = exam_date - timedelta(days=20)
        else:
            unavailable_from = exam_date - timedelta(days=30)
            
        is_late = datetime.now().date() > unavailable_from
        justification = ""
        if is_late:
            st.warning("⚠️ You are submitting this notice late (within your unavailable period).")
            justification = st.text_area("Late Notice Justification (Mandatory):")
            
        if st.button("Submit Exam Schedule"):
            if is_late and not justification:
                st.error("You must provide a justification for late notice!")
            else:
                new_exam = [user["ID"], user["Name"], exam_type, str(exam_date), str(unavailable_from), justification]
                append_row_to_sheet("exams", new_exam)
                st.success("✅ Exam schedule recorded successfully!")

    # --- WORK LOG ---
    with tab2:
        st.subheader("Daily Work & Contribution")
        
        extra_dedication = False
        why_work = ""
        assigned_by = ""
        
        if not is_avail:
            st.error(f"⚠️ {avail_text}. You are not expected to work.")
            extra_dedication = st.checkbox("🔥 Extra Dedication (I am working despite being unavailable)")
            if extra_dedication:
                why_work = st.text_input("Why do you want to work today?")
        
        if is_avail or extra_dedication:
            work_date = st.date_input("Work Date", value=datetime.today())
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.time_input("Start Time")
            with col2:
                end_time = st.time_input("End Time")
                
            core_work = st.text_area("What work did you do?")
            assigned_by = st.text_input("Who assigned/called you for this work?")
            
            if st.button("Submit Work Log"):
                t1 = datetime.combine(datetime.today(), start_time)
                t2 = datetime.combine(datetime.today(), end_time)
                if t2 < t1:
                    t2 += timedelta(days=1)
                hours_worked = round((t2 - t1).total_seconds() / 3600, 2)
                status_text = "Yes" if extra_dedication else "No"
                
                new_log = [user["ID"], user["Name"], str(work_date), str(start_time), str(end_time), hours_worked, core_work, status_text, why_work, assigned_by]
                append_row_to_sheet("work_logs", new_log)
                st.success(f"✅ Work log saved! Total calculated time: **{hours_worked} hours**.")

    # --- SUDDEN LEAVE ---
    with tab3:
        st.subheader("Sudden Work / Leave Tracker")
        leave_reason = st.text_input("Reason (e.g., Going Home, Personal Emergency)")
        
        col1, col2 = st.columns(2)
        with col1:
            start_leave = st.date_input("Start Date", key="sd")
            start_leave_time = st.time_input("Start Time", key="st")
        with col2:
            end_leave = st.date_input("End Date", key="ed")
            end_leave_time = st.time_input("End Time", key="et")
            
        if st.button("Submit Leave"):
            start_dt = datetime.combine(start_leave, start_leave_time)
            end_dt = datetime.combine(end_leave, end_leave_time)
            
            if start_dt >= end_dt:
                st.error("End date/time must be after start date/time!")
            else:
                new_leave = [user["ID"], user["Name"], leave_reason, str(start_dt), str(end_dt)]
                append_row_to_sheet("leaves", new_leave)
                st.success(f"✅ Leave marked from {start_dt.strftime('%d-%m %I:%M %p')} to {end_dt.strftime('%d-%m %I:%M %p')}.")

# ---------------------------------------------------------
# 3. ADMIN DASHBOARD
# ---------------------------------------------------------
elif menu == "Admin Panel":
    st.header("⚙️ Admin Dashboard")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    
    if admin_pass == "admin123":
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Pending Approvals", "Approved Members", "CT Records", "Final/Yearly Records", "Work Logs", "Live Availability"])
        
        users_df = load_data("users", user_cols)
        exams_df = load_data("exams", exam_cols)
        work_df = load_data("work_logs", work_cols)
        
        # --- APPROVALS ---
        with tab1:
            st.subheader("Approve New Members")
            pending = users_df[users_df["Status"] == "Pending"]
            if not pending.empty:
                for idx, row in pending.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['Name']}** - {row['Designation']} | Email: {row['Email']}")
                    if c2.button("Approve", key=f"app_{row['ID']}"):
                        users_df.loc[users_df["ID"] == row['ID'], "Status"] = "Approved"
                        update_sheet_data("users", users_df)
                        
                        email_sent = send_approval_email(row['Email'], row['Name'], row['ID'])
                        if email_sent:
                            st.success(f"Approved {row['Name']}! An official email with the ID has been sent.")
                        else:
                            st.warning(f"Approved {row['Name']}! (Email failed to send). The ID is: {row['ID']}")
                        st.rerun()
            else:
                st.info("No pending requests.")

        # --- MEMBERS DIRECTORY ---
        with tab2:
            st.subheader("All Registered Members")
            approved = users_df[users_df["Status"] == "Approved"]
            st.dataframe(approved)
            if not approved.empty:
                st.download_button("Download Members CSV", approved.to_csv(index=False).encode('utf-8'), "members.csv", "text/csv")

        # --- CT RECORDS ---
        with tab3:
            st.subheader("Class Test (CT) Data")
            ct_data = exams_df[exams_df["Exam_Type"] == "Class Test (CT)"]
            st.dataframe(ct_data)
            if not ct_data.empty:
                st.download_button("Download CT Data", ct_data.to_csv(index=False).encode('utf-8'), "ct_records.csv", "text/csv")

        # --- FINAL/YEARLY RECORDS ---
        with tab4:
            st.subheader("Final & Yearly Exam Data")
            final_data = exams_df[exams_df["Exam_Type"].isin(["Semester Final", "Yearly Exam"])]
            st.dataframe(final_data)
            if not final_data.empty:
                st.download_button("Download Final Data", final_data.to_csv(index=False).encode('utf-8'), "final_records.csv", "text/csv")

        # --- WORK LOGS ---
        with tab5:
            st.subheader("Contribution & Work Logs")
            st.dataframe(work_df)
            if not work_df.empty:
                st.download_button("Download Work Logs", work_df.to_csv(index=False).encode('utf-8'), "work_logs.csv", "text/csv")

        # --- LIVE AVAILABILITY ---
        with tab6:
            st.subheader("Live Member Availability")
            approved_users = users_df[users_df["Status"] == "Approved"]
            
            if not approved_users.empty:
                avail_data = []
                for _, u in approved_users.iterrows():
                    status_bool, status_text = check_availability(u['ID'])
                    avail_data.append({"ID": u['ID'], "Name": u['Name'], "Designation": u['Designation'], "Status": status_text})
                
                avail_df = pd.DataFrame(avail_data)
                st.dataframe(avail_df)
            else:
                st.info("No approved members yet.")
                
    elif admin_pass != "":
        st.error("Incorrect Password!")

elif menu == "My Dashboard" and not st.session_state.logged_in_user:
    st.warning("Please Login First!")
