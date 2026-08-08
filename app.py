import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
from datetime import date

# 1. Page Configuration & Custom Styling
st.set_page_config(page_title="Class 8 Dashboard Pro v2", layout="wide")

st.markdown("""
    <style>
    html { scroll-behavior: smooth; }
    .stTable, .stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #e0e0e0; }
    div[data-testid="stMetricValue"] { font-size: 22px; font-weight: 600; }
    .stButton button { border-radius: 6px; transition: all 0.3s ease; }
    .stButton button:hover { transform: translateY(-2px); }
    .profile-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
    }
    .profile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #334155;
        padding-bottom: 12px;
        margin-bottom: 16px;
    }
    .profile-name { font-size: 24px; font-weight: 700; color: #f8fafc; margin: 0; }
    .profile-roll { background-color: #3b82f6; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 600; }
    .badge-rank { background-color: #f59e0b; color: #000000; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 13px; }
    .info-label { color: #94a3b8; font-size: 13px; margin-bottom: 2px; }
    .info-value { color: #f1f5f9; font-size: 16px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# 🔑 LOGIN SYSTEM
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title("🔒 Class 8 Dashboard Pro Login")
    with st.form("login_form"):
        password = st.text_input("Enter Dashboard Password", type="password")
        submit_pass = st.form_submit_button("🔓 Log In")
        if submit_pass:
            if password == "admin123":
                st.session_state.logged_in = True
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("❌ Invalid Password!")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# Logout Sidebar
with st.sidebar:
    st.write("👤 Logged in as Teacher")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# 2. Supabase Connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Supabase Credentials `.streamlit/secrets.toml` mein check karein.")

# 3. Data Load Function (Forced 6 Subjects)
def load_data():
    try:
        response = supabase.table('class_8_students').select('*').order('roll_no').execute()
        df_data = pd.DataFrame(response.data)
        
        if not df_data.empty:
            df_data = df_data.drop_duplicates(subset=['roll_no'], keep='last')

            subject_cols = ['english', 'hindi', 'science', 'sst', 'maths', 'sanskrit', 'total_fee', 'fee_paid', 'roll_no']
            for col in subject_cols:
                if col in df_data.columns:
                    df_data[col] = pd.to_numeric(df_data[col], errors='coerce').fillna(0)
                else:
                    df_data[col] = 0

            df_data['Total Marks'] = (
                df_data['english'] + df_data['hindi'] + df_data['science'] + 
                df_data['sst'] + df_data['maths'] + df_data['sanskrit']
            )
            df_data['Percentage (%)'] = (df_data['Total Marks'] / 6).round(1)
            df_data['Rank'] = df_data['Total Marks'].rank(ascending=False, method='min').astype(int)
            df_data['Pending Fee'] = df_data['total_fee'] - df_data['fee_paid']
            
            if 'attendance' not in df_data.columns:
                df_data['attendance'] = 'Present'
            else:
                df_data['attendance'] = df_data['attendance'].fillna('Present')

            if 'date' not in df_data.columns:
                df_data['date'] = str(date.today())
            else:
                df_data['date'] = df_data['date'].fillna(str(date.today()))

            for col in ['eng_nb', 'hindi_nb', 'sci_nb', 'sst_nb', 'math_nb', 'sans_nb']:
                if col not in df_data.columns:
                    df_data[col] = 'Incomplete'
                else:
                    df_data[col] = df_data[col].fillna('Incomplete')

            for col in ['last_call_date', 'last_call_status', 'call_remarks']:
                if col not in df_data.columns:
                    df_data[col] = 'No Call Logged'
                else:
                    df_data[col] = df_data[col].fillna('No Call Logged')
            
        return df_data
    except Exception as e:
        st.error(f"Data loading error: {e}")
        return pd.DataFrame()

df = load_data()

st.title("📚 Class 8 Teacher Dashboard Pro (6 Subjects)")

def save_student_data(r_no, s_name, f_name, p_mobile, att_status, att_pct, cond, eng_m, hin_m, sci_m, sst_m, math_m, sans_m, t_fee, f_paid, entry_date):
    if not s_name.strip():
        st.error("⚠️ Student Name bharna zaroori hai!")
        return False
    try:
        data = {
            "roll_no": int(r_no),
            "name": s_name.strip(),
            "father_name": f_name.strip(),
            "parent_mobile": str(p_mobile).strip(),
            "attendance": att_status,
            "attendance_%": int(att_pct),
            "conduct": cond,
            "english": int(eng_m),
            "hindi": int(hin_m),
            "science": int(sci_m),
            "sst": int(sst_m),
            "maths": int(math_m),
            "sanskrit": int(sans_m),
            "total_fee": float(t_fee),
            "fee_paid": float(f_paid),
            "date": str(entry_date)
        }
        supabase.table('class_8_students').upsert(data, on_conflict="roll_no").execute()
        st.success(f"✅ Student '{s_name}' (Roll No: {r_no}) ka record save ho gaya!")
        return True
    except Exception as err:
        st.error(f"❌ Error while saving: {err}")
        return False

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Student Data Register",
    "📊 Academic Results Register", 
    "👤 Pro Profiles & WhatsApp", 
    "💳 Fee Details",
    "📞 Parent Call Logs",
    "📓 Notebook Tracker"
])

# TAB 1: Register
with tab1:
    with st.expander("➕ Add / Edit Student Record", expanded=False):
        with st.form("quick_add_form", clear_on_submit=True):
            st.markdown("##### 📝 Student Details & Daily Attendance")
            
            r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1, 2, 2, 2])
            with r1_c1:
                q_rno = st.number_input("Roll No *", min_value=1, step=1, value=len(df)+1 if not df.empty else 1, key="q_rno")
            with r1_c2:
                q_name = st.text_input("Student Name *", key="q_name")
            with r1_c3:
                q_fname = st.text_input("Father Name", key="q_fname")
            with r1_c4:
                q_date = st.date_input("Date 📅", value=date.today(), key="q_date")

            r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
            with r2_c1:
                q_mobile = st.text_input("Parent Mobile", key="q_mobile")
            with r2_c2:
                q_att_status = st.selectbox("Today's Attendance Status 📍", ["Present", "Absent", "Leave"], key="q_att_status")
            with r2_c3:
                q_att_pct = st.number_input("Overall Attendance (%)", 0, 100, 90, key="q_att_pct")
            with r2_c4:
                q_cond = st.selectbox("Conduct", ["Good", "Excellent", "Outstanding", "Needs Improvement"], key="q_cond")

            st.markdown("##### 📚 Academic Marks (6 Subjects) & Fee Details")
            r3_c1, r3_c2, r3_c3 = st.columns(3)
            with r3_c1:
                q_eng = st.number_input("1. English Marks", 0, 100, 0, key="q_eng")
                q_hin = st.number_input("2. Hindi Marks", 0, 100, 0, key="q_hin")
            with r3_c2:
                q_sci = st.number_input("3. Science Marks", 0, 100, 0, key="q_sci")
                q_sst = st.number_input("4. Social Science Marks", 0, 100, 0, key="q_sst")
            with r3_c3:
                q_math = st.number_input("5. Maths Marks", 0, 100, 0, key="q_math")
                q_sans = st.number_input("6. Sanskrit Marks", 0, 100, 0, key="q_sans")

            r4_c1, r4_c2 = st.columns(2)
            with r4_c1:
                q_tfee = st.number_input("Total Fee (₹)", min_value=0.0, value=15000.0, key="q_tfee")
            with r4_c2:
                q_fpaid = st.number_input("Fee Paid (₹)", min_value=0.0, value=0.0, key="q_fpaid")

            q_submitted = st.form_submit_button("💾 Save / Update Student Data")
            if q_submitted:
                if save_student_data(q_rno, q_name, q_fname, q_mobile, q_att_status, q_att_pct, q_cond, q_eng, q_hin, q_sci, q_sst, q_math, q_sans, q_tfee, q_fpaid, q_date):
                    st.rerun()

    st.markdown("---")
    st.subheader("📋 Class 8 Student Information & Attendance Register")
    
    if not df.empty:
        reg_cols = ['roll_no', 'name', 'father_name', 'parent_mobile', 'date', 'attendance', 'attendance_%', 'conduct']
        available_reg_cols = [c for c in reg_cols if c in df.columns]
        sorted_reg_df = df.sort_values(by='roll_no')[available_reg_cols]
        st.dataframe(sorted_reg_df, use_container_width=True, hide_index=True)
    else:
        st.info("Abhi koi student add nahi hai. Upar '+' button par click karke student add karein.")

# TAB 2: Results
with tab2:
    st.subheader("📊 Class 8 Academic Results & Rank Register")
    
    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Students", len(df))
        m2.metric("Class Average Percentage", f"{df['Percentage (%)'].mean():.1f}%")
        top_scorer = df.loc[df['Total Marks'].idxmax()]
        m3.metric("Class Topper 🏆", f"{top_scorer['name']} ({top_scorer['Total Marks']}/600)")

        st.markdown("---")

        def highlight_performance(val):
            if isinstance(val, (int, float)):
                if val >= 75: 
                    return 'background-color: #d4edda; color: #155724;'
                elif val < 40: 
                    return 'background-color: #f8d7da; color: #721c24;'
            return ''

        result_cols = ['Rank', 'roll_no', 'name', 'english', 'hindi', 'science', 'sst', 'maths', 'sanskrit', 'Total Marks', 'Percentage (%)']
        available_res_cols = [c for c in result_cols if c in df.columns]
        
        sorted_res_df = df.sort_values(by='Rank')[available_res_cols]
        styled_res_df = sorted_res_df.style.map(highlight_performance, subset=['english', 'hindi', 'science', 'sst', 'maths', 'sanskrit', 'Percentage (%)'])
        st.dataframe(styled_res_df, use_container_width=True, hide_index=True)
    else:
        st.info("Results dekhne ke liye pehle Student Data Register tab mein student record add karein.")

# TAB 3: WhatsApp Profile
with tab3:
    st.subheader("👤 Student Profile Pro Card")
    
    if not df.empty:
        if 'student_idx' not in st.session_state:
            st.session_state.student_idx = 0

        if st.session_state.student_idx >= len(df):
            st.session_state.student_idx = 0

        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("⬅️ Pichla Student", use_container_width=True):
                if st.session_state.student_idx > 0:
                    st.session_state.student_idx -= 1
                    st.rerun()

        with col_next:
            if st.button("Agle Student ➔", use_container_width=True):
                if st.session_state.student_idx < len(df) - 1:
                    st.session_state.student_idx += 1
                    st.rerun()

        student = df.iloc[st.session_state.student_idx]
        
        with col_info:
            st.info(f"Viewing Profile {st.session_state.student_idx + 1} of {len(df)}")

        st.markdown(f"""
            <div class="profile-card">
                <div class="profile-header">
                    <div>
                        <span class="profile-name">👤 {student.get('name', 'N/A')}</span>
                        <span style="margin-left: 10px;" class="badge-rank">🏆 Rank #{student.get('Rank', 'N/A')}</span>
                    </div>
                    <div>
                        <span class="profile-roll">Roll No: #{int(student.get('roll_no', 0))}</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <div class="info-label">Father's Name</div>
                        <div class="info-value">{student.get('father_name', 'N/A')}</div>
                    </div>
                    <div>
                        <div class="info-label">Date</div>
                        <div class="info-value">📅 {student.get('date', 'N/A')}</div>
                    </div>
                    <div>
                        <div class="info-label">Status</div>
                        <div class="info-value">📌 {student.get('attendance', 'Present')}</div>
                    </div>
                    <div>
                        <div class="info-label">Parent Mobile</div>
                        <div class="info-value">📱 {student.get('parent_mobile', 'N/A')}</div>
                    </div>
                    <div>
                        <div class="info-label">Attendance %</div>
                        <div class="info-value">🗓️ {student.get('attendance_%', 0)}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7 = st.columns(7)
        m_col1.metric("English", f"{student.get('english', 0)}/100")
        m_col2.metric("Hindi", f"{student.get('hindi', 0)}/100")
        m_col3.metric("Science", f"{student.get('science', 0)}/100")
        m_col4.metric("SST", f"{student.get('sst', 0)}/100")
        m_col5.metric("Maths", f"{student.get('maths', 0)}/100")
        m_col6.metric("Sanskrit", f"{student.get('sanskrit', 0)}/100")
        m_col7.metric("Total Score", f"{student.get('Total Marks', 0)}/600", f"{student.get('Percentage (%)', 0)}%")

        st.markdown("---")

        st.markdown("##### 📲 Direct WhatsApp Share")
        default_mobile = str(student.get('parent_mobile', '')).strip()
        if default_mobile and not default_mobile.startswith("91"):
            default_mobile = "91" + default_mobile
        elif not default_mobile:
            default_mobile = "91"

        msg_text = f"Namaste! Class 8 Update for *{student.get('name', '')}* (Date: {student.get('date', '')}):\n\n" \
                   f"🏆 *Class Rank:* #{student.get('Rank', 'N/A')}\n" \
                   f"📌 *Today's Attendance Status:* {student.get('attendance', 'Present')}\n" \
                   f"📊 *Total Marks:* {student.get('Total Marks', 0)}/600 ({student.get('Percentage (%)', 0)}%)\n\n" \
                   f"*Subject Breakdown:*\n" \
                   f"- English: {student.get('english', 0)}\n" \
                   f"- Hindi: {student.get('hindi', 0)}\n" \
                   f"- Science: {student.get('science', 0)}\n" \
                   f"- Social Science: {student.get('sst', 0)}\n" \
                   f"- Maths: {student.get('maths', 0)}\n" \
                   f"- Sanskrit: {student.get('sanskrit', 0)}\n\n" \
                   f"🗓️ *Overall Attendance:* {student.get('attendance_%', 0)}%\n" \
                   f"⭐ *Conduct:* {student.get('conduct', 'Good')}\n\n" \
                   f"Thank you!"

        encoded_msg = urllib.parse.quote(msg_text)
        whatsapp_url = f"https://wa.me/{default_mobile}?text={encoded_msg}"

        st.link_button("💬 WhatsApp Par Result Send Karein", whatsapp_url, use_container_width=True)

    else:
        st.info("Abhi koi student profile show karne ke liye data available nahi hai.")

# TAB 4: Fee Details
with tab4:
    st.subheader("💳 Student Fee Details Register")
    if not df.empty:
        f1, f2, f3 = st.columns(3)
        f1.metric("Total Expected Fees", f"₹{df['total_fee'].sum():,.2f}")
        f2.metric("Total Collected Fees", f"₹{df['fee_paid'].sum():,.2f}")
        f3.metric("Total Pending Fees ⚠️", f"₹{df['Pending Fee'].sum():,.2f}")

        st.markdown("---")

        fee_cols = ['roll_no', 'name', 'father_name', 'parent_mobile', 'total_fee', 'fee_paid', 'Pending Fee']
        fee_df = df[[c for c in fee_cols if c in df.columns]]
        st.dataframe(fee_df, use_container_width=True, hide_index=True)
    else:
        st.info("Abhi koi student register nahi hua hai.")

# TAB 5: Call Logs
with tab5:
    st.subheader("📞 Parent Call Communication Log")
    
    if not df.empty:
        selected_student_call = st.selectbox(
            "Select Student for Call Logging:",
            options=df['roll_no'].tolist(),
            format_func=lambda x: f"Roll No {x}: {df[df['roll_no']==x]['name'].values[0]}"
        )
        
        student_info = df[df['roll_no'] == selected_student_call].iloc[0]

        st.info(f"**Parent Mobile:** 📱 {student_info.get('parent_mobile', 'N/A')} | **Father Name:** {student_info.get('father_name', 'N/A')}")

        with st.form("call_log_form"):
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                call_status = st.selectbox("Call Status 📲", ["Connected - Discovered Issue", "Connected - Satisfied", "Unreachable", "Switched Off / Busy", "Follow-up Scheduled"])
            with c_col2:
                call_date = st.date_input("Call Date 📅", value=date.today())

            call_remarks = st.text_area("Call Discussion / Remarks 📝", placeholder="Discussed absenteeism, homework delay, performance etc...")
            submit_call = st.form_submit_button("💾 Save Call Log")

            if submit_call:
                try:
                    update_data = {
                        "last_call_date": str(call_date),
                        "last_call_status": call_status,
                        "call_remarks": call_remarks.strip()
                    }
                    supabase.table('class_8_students').update(update_data).eq('roll_no', int(selected_student_call)).execute()
                    st.success(f"✅ Call Log updated for {student_info['name']}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error updating call log: {e}")

        st.markdown("---")
        st.subheader("📑 Parent Call Logs History")
        call_cols = ['roll_no', 'name', 'parent_mobile', 'last_call_date', 'last_call_status', 'call_remarks']
        call_df = df[[c for c in call_cols if c in df.columns]]
        st.dataframe(call_df, use_container_width=True, hide_index=True)

    else:
        st.info("No student available for logging calls.")

# TAB 6: Notebook Tracker
with tab6:
    st.subheader("📓 Subject-wise Notebook Checking Tracker")
    
    if not df.empty:
        selected_student_nb = st.selectbox(
            "Select Student to Update Notebook Status:",
            options=df['roll_no'].tolist(),
            format_func=lambda x: f"Roll No {x}: {df[df['roll_no']==x]['name'].values[0]}"
        )
        
        s_nb_info = df[df['roll_no'] == selected_student_nb].iloc[0]

        with st.form("nb_tracker_form"):
            nb_opts = ["Complete", "Incomplete", "Pending Checking"]
            
            nb_c1, nb_c2, nb_c3 = st.columns(3)
            with nb_c1:
                eng_nb = st.selectbox("English Notebook 📖", nb_opts, index=nb_opts.index(s_nb_info.get('eng_nb', 'Incomplete')) if s_nb_info.get('eng_nb') in nb_opts else 1)
                hin_nb = st.selectbox("Hindi Notebook 📚", nb_opts, index=nb_opts.index(s_nb_info.get('hindi_nb', 'Incomplete')) if s_nb_info.get('hindi_nb') in nb_opts else 1)
            with nb_c2:
                sci_nb = st.selectbox("Science Notebook 🔬", nb_opts, index=nb_opts.index(s_nb_info.get('sci_nb', 'Incomplete')) if s_nb_info.get('sci_nb') in nb_opts else 1)
                sst_nb = st.selectbox("SST Notebook 🌍", nb_opts, index=nb_opts.index(s_nb_info.get('sst_nb', 'Incomplete')) if s_nb_info.get('sst_nb') in nb_opts else 1)
            with nb_c3:
                math_nb = st.selectbox("Maths Notebook 📐", nb_opts, index=nb_opts.index(s_nb_info.get('math_nb', 'Incomplete')) if s_nb_info.get('math_nb') in nb_opts else 1)
                sans_nb = st.selectbox("Sanskrit Notebook 📜", nb_opts, index=nb_opts.index(s_nb_info.get('sans_nb', 'Incomplete')) if s_nb_info.get('sans_nb') in nb_opts else 1)

            submit_nb = st.form_submit_button("💾 Update Notebook Status")

            if submit_nb:
                try:
                    update_nb_data = {
                        "eng_nb": eng_nb,
                        "hindi_nb": hin_nb,
                        "sci_nb": sci_nb,
                        "sst_nb": sst_nb,
                        "math_nb": math_nb,
                        "sans_nb": sans_nb
                    }
                    supabase.table('class_8_students').update(update_nb_data).eq('roll_no', int(selected_student_nb)).execute()
                    st.success(f"✅ Notebook status updated for {s_nb_info['name']}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error updating notebook status: {e}")

        st.markdown("---")
        st.subheader("📋 Class Notebook Status Summary")

        def highlight_nb(val):
            if val == 'Complete':
                return 'background-color: #d4edda; color: #155724;'
            elif val == 'Incomplete':
                return 'background-color: #f8d7da; color: #721c24;'
            elif val == 'Pending Checking':
                return 'background-color: #fff3cd; color: #856404;'
            return ''

        nb_cols = ['roll_no', 'name', 'eng_nb', 'hindi_nb', 'sci_nb', 'sst_nb', 'math_nb', 'sans_nb']
        nb_df = df[[c for c in nb_cols if c in df.columns]]
        styled_nb_df = nb_df.style.map(highlight_nb, subset=[c for c in ['eng_nb', 'hindi_nb', 'sci_nb', 'sst_nb', 'math_nb', 'sans_nb'] if c in nb_df.columns])
        st.dataframe(styled_nb_df, use_container_width=True, hide_index=True)

    else:
        st.info("No student data available for Notebook Tracking.")
