import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date, time
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v4.csv"
CONFIG_FILE = "shop_config_v4.csv"
ADMIN_PASSWORD = "tfboys0921"

# 初始化資料結構
COLS = ["日期", "開始時間", "結束時間", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"]
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 初始化店家設定 (項目、時間、價格)
if not os.path.exists(CONFIG_FILE):
    default_services = pd.DataFrame({
        "項目名稱": ["美甲設計", "美睫嫁接", "霧眉"],
        "操作分鐘": [90, 60, 180],
        "價格": [1200, 800, 5000]
    })
    default_services.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

def load_data():
    return pd.read_csv(DATA_FILE, encoding="utf-8-sig").astype(str)

def load_config():
    return pd.read_csv(CONFIG_FILE, encoding="utf-8-sig")

# --- 介面開始 ---
st.set_page_config(page_title="專業美業管理系統 v4.0", layout="wide")
df = load_data()
config_df = load_config()

st.sidebar.title("🎀 美業預約系統")
mode = st.sidebar.radio("切換模式", ["👤 客戶預約月曆", "🔐 店家管理後台"])

# 共用月曆設定 (中文版)
CALENDAR_OPTIONS = {
    "editable": False,
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "timeGridWeek,timeGridDay,dayGridMonth",
    },
    "buttonText": {
        "today": "今天",
        "month": "月",
        "week": "週",
        "day": "日"
    },
    "locale": "zh-tw",  # 強制中文
    "slotMinTime": "10:00:00", # 營業開始
    "slotMaxTime": "21:00:00", # 營業結束
    "allDaySlot": False,
}

if mode == "👤 客戶預約月曆":
    st.header("🗓️ 選擇您的預約時間")
    st.info("請先從下方月曆中點選您想要的『🟢 可預約時段』，再填寫資料。")

    col1, col2 = st.columns([2, 1])

    with col1:
        # 生成可預約空檔視圖
        booked_events = []
        for _, row in df.iterrows():
            if row["狀態"] != "已取消":
                booked_events.append({
                    "title": "🔴 已被預約",
                    "start": f"{row['日期']}T{row['開始時間']}:00",
                    "end": f"{row['日期']}T{row['結束時間']}:00",
                    "color": "#E74C3C",
                })
        
        # 顯示月曆
        st.subheader("點選理想時段：")
        client_cal = calendar(events=booked_events, options={**CALENDAR_OPTIONS, "initialView": "timeGridWeek"})
        
        # 抓取點擊的時間
        click_start = ""
        if "callback" in client_cal and client_cal["callback"] == "dateClick":
            click_start = client_cal["dateClick"]["date"].split("+")[0]
        elif "callback" in client_cal and client_cal["callback"] == "select":
            click_start = client_cal["select"]["start"].split("+")[0]

    with col2:
        st.subheader("✍️ 填寫預約單")
        with st.form("client_booking_form"):
            if click_start:
                try:
                    dt_obj = datetime.strptime(click_start, "%Y-%m-%dT%H:%M:%S")
                    st.success(f"已選取：{dt_obj.strftime('%Y-%m-%d %H:%M')}")
                    sel_d = dt_obj.date()
                    sel_t = dt_obj.strftime("%H:%M")
                except:
                    sel_d, sel_t = date.today(), "10:00"
            else:
                st.warning("請先在左邊月曆上『點擊』時間點")
                sel_d, sel_t = date.today(), "10:00"

            name = st.text_input("客人姓名*")
            phone = st.text_input("聯絡電話*")
            gender = st.radio("性別", ["女", "男"], horizontal=True)
            service_option = st.selectbox("施作項目", config_df["項目名稱"].tolist())
            
            # 獲取價格與時長
            s_info = config_df[config_df["項目名稱"] == service_option].iloc[0]
            st.caption(f"💰 價格: ${s_info['價格']} | ⏳ 時長: {s_info['操作分鐘']}分")
            
            note = st.text_area("備註")
            submit = st.form_submit_button("確認提交預約")

        if submit:
            if not click_start:
                st.error("請先在月曆上選擇時段！")
            elif not name or not phone:
                st.error("請填妥姓名與電話！")
            else:
                start_dt = datetime.combine(sel_d, datetime.strptime(sel_t, "%H:%M").time())
                end_dt = start_dt + timedelta(minutes=int(s_info['操作分鐘']))
                
                # 簡單重疊檢查
                new_row = [str(sel_d), sel_t, end_dt.strftime("%H:%M"), name, gender, service_option, phone, str(s_info['價格']), "預約中", note]
                pd.concat([load_data(), pd.DataFrame([new_row], columns=COLS)]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("🎉 預約成功！我們將會與您聯繫確認。")
                st.balloons()

else:
    # --- 店家管理後台 ---
    pwd = st.sidebar.text_input("後台密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["📅 管理行事曆", "⚙️ 項目與價格設定", "📋 訂單總表管理"])
        
        with tab1:
            st.subheader("店家專屬排程檢視")
            admin_events = []
            for _, row in df.iterrows():
                if row["狀態"] != "已取消":
                    admin_events.append({
                        "title": f"{row['客人姓名']} | {row['項目']}",
                        "start": f"{row['日期']}T{row['開始時間']}:00",
                        "end": f"{row['日期']}T{row['結束時間']}:00",
                        "color": "#FF69B4" if row["性別"] == "女" else "#4169E1",
                        "description": row["備註"]
                    })
            calendar(events=admin_events, options={**CALENDAR_OPTIONS, "initialView": "dayGridMonth"})

        with tab2:
            st.subheader("服務項目設定")
            new_config = st.data_editor(config_df, num_rows="dynamic", use_container_width=True)
            if st.button("更新設定"):
                new_config.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
                st.success("設定已同步。")

        with tab3:
            st.subheader("歷史資料編輯")
            curr_df = load_data()
            updated_df = st.data_editor(curr_df, use_container_width=True, num_rows="dynamic")
            if st.button("儲存資料內容"):
                updated_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("資料庫已更新！")
    elif pwd != "":
        st.error("密碼錯誤")
