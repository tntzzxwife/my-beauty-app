import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- 基礎設定 ---
DATA_FILE = "appointments.csv"
CONFIG_FILE = "config.csv" # 儲存後台設定
COLS = ["日期", "時段", "客人姓名", "電話", "LINE暱稱", "施作項目", "推薦人", "金額", "狀態", "備註"]
ADMIN_PASSWORD = "666"

# 初始化資料
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 初始化後台設定 (預設開放時段)
if not os.path.exists(CONFIG_FILE):
    default_config = pd.DataFrame({"key": ["open_times"], "value": ["10:00,11:00,13:00,14:00,15:00,16:00,17:00,18:00,19:00,20:00"]})
    default_config.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

def load_data():
    return pd.read_csv(DATA_FILE, encoding="utf-8-sig").astype(str)

def get_config():
    conf = pd.read_csv(CONFIG_FILE, encoding="utf-8-sig")
    return conf.loc[conf['key'] == 'open_times', 'value'].values[0].split(',')

# --- 介面開始 ---
st.set_page_config(page_title="專業美容管理系統 v2.0", layout="wide")

df = load_data()
open_times = get_config()

mode = st.sidebar.radio("切換模式", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.header("✨ 美容工作室預約")
    st.markdown("---")
    
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("選擇預約日期", min_value=date.today())
            name = st.text_input("客人姓名*")
            line_id = st.text_input("您的 LINE 暱稱* (以便聯繫)")
        with col2:
            # 過濾已約時段
            booked_times = df[(df["日期"] == str(selected_date)) & (df["狀態"] != "已取消")]["時段"].tolist()
            available_times = [t for t in open_times if t not in booked_times]
            selected_time = st.selectbox("選擇預約時段*", available_times if available_times else ["當日已滿"])
            phone = st.text_input("聯絡電話*")
            referrer = st.text_input("推薦人 (選填)")

        service = st.selectbox("施作項目", ["美甲", "美睫", "護膚", "紋繡", "其他"])
        note = st.text_area("備註說明")
        
        if st.form_submit_button("提交預約"):
            if not (name and phone and line_id) or selected_time == "當日已滿":
                st.error("請填寫必填欄位 (*) 且確保時段尚未被預約。")
            else:
                new_row = [str(selected_date), selected_time, name, phone, line_id, service, referrer, "0", "預約中", note]
                new_df = pd.DataFrame([new_row], columns=COLS)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                
                st.success(f"✅ 預約提交成功！")
                st.info(f"請點擊下方按鈕加入我們的 LINE 並傳送您的姓名：{name}，我們將為您確認。")
                # 這裡可以放你的 LINE 官方帳號連結
                st.markdown("[👉 點我加入店家 LINE](https://line.me/ti/p/你的ID)")

else:
    # --- 店家管理後台 ---
    st.header("🔐 店家管理後台")
    pwd = st.sidebar.text_input("管理密碼", type="password")
    
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 月曆檢視", "👥 客戶檔案紀錄", "⚙️ 時段與設定", "📋 原始資料管理"])
        
        with tab1:
            st.subheader("本月預約分佈")
            view_date = st.date_input("查看日期詳情", date.today())
            day_detail = df[df["日期"] == str(view_date)]
            if not day_detail.empty:
                st.table(day_detail[["時段", "客人姓名", "LINE暱稱", "施作項目", "推薦人"]])
            else:
                st.write("這天目前沒有人預約喔～")

        with tab2:
            st.subheader("👤 客戶消費紀錄彙整")
            # 依姓名與電話彙整客人資料
            customer_summary = df.groupby(['客人姓名', '電話', 'LINE暱稱']).agg({
                '日期': 'count',
                '金額': lambda x: pd.to_numeric(x, errors='coerce').sum(),
                '推薦人': lambda x: ', '.join(set(x.dropna()))
            }).rename(columns={'日期': '預約次數', '金額': '總消費額'})
            st.dataframe(customer_summary, use_container_width=True)

        with tab3:
            st.subheader("⚙️ 營業時段調整")
            current_times_str = ",".join(open_times)
            new_times_input = st.text_area("設定開放時段 (用半型逗號隔開)", current_times_str)
            if st.button("儲存時段設定"):
                conf_df = pd.DataFrame({"key": ["open_times"], "value": [new_times_input]})
                conf_df.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
                st.success("時段已更新！")
                st.rerun()

        with tab4:
            st.subheader("📋 訂單編輯與刪除")
            # 可以在這裡編輯金額
            edit_df = df.copy()
            st.data_editor(edit_df, key="data_editor_table") 
            if st.button("更新所有修改內容"):
                st.session_state["data_editor_table"]["edited_rows"] # 這裡可以寫入更複雜的編輯逻辑
                edit_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("資料已同步！")

    elif pwd != "":
        st.error("密碼錯誤")
