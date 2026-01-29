import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from streamlit_calendar import calendar
import os

# --- 基礎設定與密碼 ---
DATA_FILE = "appointments_v3.csv"
CONFIG_FILE = "shop_config.csv"
ADMIN_PASSWORD = "tfboys0921"

# 初始化資料結構 (新增性別、結束時間)
COLS = ["日期", "開始時間", "結束時間", "客人姓名", "性別", "項目", "電話", "狀態", "備註"]

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 初始化店家設定 (預設項目與操作時間)
if not os.path.exists(CONFIG_FILE):
    default_services = pd.DataFrame({
        "項目名稱": ["美甲設計", "美睫嫁接", "霧眉"],
        "操作分鐘": [90, 60, 120]
    })
    default_services.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

def load_data():
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig").astype(str)
    return df

def load_config():
    return pd.read_csv(CONFIG_FILE, encoding="utf-8-sig")

# --- 介面開始 ---
st.set_page_config(page_title="專業美業管理系統 v3.0", layout="wide")
df = load_data()
config_df = load_config()

st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.header("✨ 線上預約系統")
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("選擇日期", min_value=date.today())
            name = st.text_input("客人姓名*")
            gender = st.radio("性別", ["女", "男", "其他"], horizontal=True)
            phone = st.text_input("聯絡電話*")
        with col2:
            service_option = st.selectbox("施作項目", config_df["項目名稱"].tolist())
            t = st.time_input("預約起始時間", datetime.strptime("10:00", "%H:%M"))
            note = st.text_area("備註")
        
        if st.form_submit_button("提交預約"):
            # 計算結束時間
            duration = config_df[config_df["項目名稱"] == service_option]["操作分鐘"].values[0]
            start_dt = datetime.combine(d, t)
            end_dt = start_dt + timedelta(minutes=int(duration))
            
            new_row = [str(d), start_dt.strftime("%H:%M"), end_dt.strftime("%H:%M"), name, gender, service_option, phone, "已預約", note]
            new_df = pd.DataFrame([new_row], columns=COLS)
            pd.concat([df, new_df]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.success(f"✅ 預約成功！預計施作至 {end_dt.strftime('%H:%M')}")
            st.balloons()

else:
    # --- 店家管理後台 ---
    pwd = st.sidebar.text_input("後台密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["📅 預約月曆檢視", "⚙️ 項目與時間設定", "📋 原始資料管理"])
        
        with tab1:
            st.subheader("月曆預約排程")
            # 轉換為月曆格式
            calendar_events = []
            for _, row in df.iterrows():
                if row["狀態"] != "已取消":
                    calendar_events.append({
                        "title": f"{row['客人姓名']}({row['性別']}) - {row['項目']}",
                        "start": f"{row['日期']}T{row['開始時間']}:00",
                        "end": f"{row['日期']}T{row['結束時間']}:00",
                        "color": "#FF69B4" if row["性別"] == "女" else "#4169E1"
                    })
            
            calendar_options = {
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek,timeGridDay"},
                "initialView": "dayGridMonth",
            }
            calendar(events=calendar_events, options=calendar_options)

        with tab2:
            st.subheader("設定您的美業項目")
            new_config = st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
            if st.button("儲存項目設定"):
                new_config.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
                st.success("設定已更新！")

        with tab3:
            st.subheader("訂單管理")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
            if st.button("儲存變更"):
                edited_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.rerun()
    elif pwd != "":
        st.error("密碼錯誤")
