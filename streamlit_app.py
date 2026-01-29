import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

def get_calendar_service():
    # 讀取剛剛設定的 Secrets
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/calendar'])
    return build('calendar', 'v3', credentials=scoped_creds)

st.set_page_config(page_title="專業預約系統", layout="centered")
st.markdown("<h1 style='text-align: center; color: #D44E7D;'>🌸 美業自動化預約系統 🌸</h1>", unsafe_allow_html=True)

with st.form("booking_form"):
    d = st.date_input("📅 選擇預約日期")
    t = st.radio("🕒 選擇時段", ["14:00", "16:00", "18:00"], horizontal=True)
    name = st.text_input("客人姓名*")
    line_n = st.text_input("LINE 暱稱*")
    phone = st.text_input("手機號碼*")
    items = st.multiselect("施作項目*", ["美甲", "美睫", "保養", "霧眉"])
    
    if st.form_submit_button("🚀 確定預約 (直接存入月曆)"):
        if name and line_n and items:
            try:
                service = get_calendar_service()
                start_dt = f"{d}T{t}:00"
                # 設為兩小時後結束
                end_hour = int(t[:2]) + 2
                end_dt = f"{d}T{end_hour:02}:00:00"
                
                event = {
                    'summary': f'💖 預約：{name} ({line_n})',
                    'description': f'電話：{phone}\n項目：{", ".join(items)}',
                    'start': {'dateTime': start_dt, 'timeZone': 'Asia/Taipei'},
                    'end': {'dateTime': end_dt, 'timeZone': 'Asia/Taipei'},
                }
                
                # 寫入你的主日曆
                service.events().insert(calendarId='karry0921jackson1128@gmail.com', body=event).execute()
                st.success("🎉 預約成功！資料已直接存入您的 Google 日曆。")
                st.balloons()
            except Exception as e:
                st.error(f"❌ 寫入失敗，請檢查日曆分享權限或 Secrets：{e}")
        else:
            st.warning("請填寫所有必要欄位。")
