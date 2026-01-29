import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_calendar import calendar
import os

# --- 基礎設定 ---
DATA_FILE = "appointments_v5.csv"
CONFIG_FILE = "shop_config_v5.csv"
ADMIN_PASSWORD = "tfboys0921"
FIXED_SLOTS = ["14:00", "16:00", "18:00"] # 您要求的固定時段

# 初始化資料
COLS = ["日期", "時段", "客人姓名", "性別", "項目", "電話", "金額", "狀態", "備註"]
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

if not os.path.exists(CONFIG_FILE):
    pd.DataFrame({
        "項目名稱": ["美甲設計", "美睫嫁接", "霧眉"],
        "價格": [1200, 800, 5000]
    }).to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

def load_data():
    return pd.read_csv(DATA_FILE, encoding="utf-8-sig").astype(str)

def load_config():
    return pd.read_csv(CONFIG_FILE, encoding="utf-8-sig")

# --- 介面開始 ---
st.set_page_config(page_title="專業美業預約系統", layout="wide")
df = load_data()
config_df = load_config()

st.sidebar.title("🎀 系統選單")
mode = st.sidebar.radio("切換模式", ["👤 客戶預約看空檔", "🔐 店家管理後台"])

if mode == "👤 客戶預約看空檔":
    st.title("📅 線上預約掛號")
    st.info("請從下方月曆查看哪天有空（顯示餘幾位），點擊日期後於右側填寫資料。")

    col_cal, col_form = st.columns([2, 1])

    with col_cal:
        # 計算每天剩餘名額並顯示在月曆上
        active_df = df[df["狀態"] != "已取消"]
        daily_counts = active_df.groupby("日期").size()
        
        # 建立未來 30 天的事件提醒
        event_list = []
        for i in range(0, 45):
            d = date.today() + pd.Timedelta(days=i)
            d_str = str(d)
            booked_count = daily_counts.get(d_str, 0)
            remaining = len(FIXED_SLOTS) - booked_count
            
            if remaining > 0:
                event_list.append({
                    "title": f"🟢 餘 {remaining}",
                    "start": d_str,
                    "allDay": True,
                    "color": "#2ECC71"
                })
            else:
                event_list.append({
                    "title": "🔴 已滿",
                    "start": d_str,
                    "allDay": True,
                    "color": "#E74C3C"
                })

        cal_options = {
            "locale": "zh-tw",
            "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
            "selectable": True,
        }
        state = calendar(events=event_list, options=cal_options, key="customer_cal")

    with col_form:
        st.subheader("✍️ 預約資料")
        
        # 獲取點擊日期
        selected_date_str = str(date.today())
        if state.get("callback") == "dateClick":
            selected_date_str = state["dateClick"]["date"].split("T")[0]
        elif state.get("callback") == "select":
            selected_date_str = state["select"]["start"].split("T")[0]
            
        st.write(f"📅 預約日期：**{selected_date_str}**")
        
        # 過濾該日期可選時段
        day_booked = df[(df["日期"] == selected_date_str) & (df["狀態"] != "已取消")]["時段"].tolist()
        available_slots = [s for s in FIXED_SLOTS if s not in day_booked]

        with st.form("booking_form", clear_on_submit=True):
            if not available_slots:
                st.error("⚠️ 該日已無可預約時段，請選其他天。")
                sel_time = None
            else:
                sel_time = st.selectbox("選擇時段", available_slots)
            
            name = st.text_input("客人姓名*")
            phone = st.text_input("聯絡電話*")
            gender = st.radio("性別", ["女", "男"], horizontal=True)
            service = st.selectbox("施作項目", config_df["項目名稱"].tolist())
            
            price = config_df[config_df["項目名稱"] == service]["價格"].values[0]
            st.write(f"💰 預計金額：${price}")
            
            note = st.text_area("備註")
            submit = st.form_submit_button("確認預約")

            if submit:
                if not sel_time:
                    st.error("請選擇有效時段")
                elif not name or not phone:
                    st.error("姓名與電話為必填")
                else:
                    new_data = [selected_date_str, sel_time, "-", name, gender, service, phone, str(price), "預約中", note]
                    new_df = pd.DataFrame([new_data], columns=COLS)
                    pd.concat([load_data(), new_df]).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.success("🎉 預約成功！")
                    st.balloons()

else:
    # --- 店家管理後台 ---
    pwd = st.sidebar.text_input("管理密碼", type="password")
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["📊 行事曆管理", "🛠️ 項目價格調整", "📑 所有訂單清單"])
        
        with tab1:
            admin_events = []
            for _, r in df.iterrows():
                if r["狀態"] != "已取消":
                    admin_events.append({
                        "title": f"{r['時段']} {r['客人姓名']}-{r['項目']}",
                        "start": r["日期"],
                        "color": "#FF69B4" if r["性別"] == "女" else "#4169E1"
                    })
            calendar(events=admin_events, options={"locale": "zh-tw"})

        with tab2:
            new_conf = st.data_editor(config_df, num_rows="dynamic")
            if st.button("儲存項目設定"):
                new_conf.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
                st.success("更新成功")

        with tab3:
            raw_df = load_data()
            updated_df = st.data_editor(raw_df, num_rows="dynamic")
            if st.button("儲存數據變更"):
                updated_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("同步完成")
    elif pwd != "":
        st.error("密碼不正確")
