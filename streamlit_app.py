import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- 基礎設定 ---
DATA_FILE = "appointments.csv"
CONFIG_FILE = "config.csv" # 儲存後台設定
COLS = ["日期", "時段", "客人姓名", "電話", "LINE暱稱", "施作項目", "推薦人", "金額", "狀態", "備註"]
ADMIN_PASSWORD = "tfboys0921"  # 已成功更新密碼

# 初始化資料
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=COLS).to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# 初始化後台設定 (預設開放時段)
if not os.path.exists(CONFIG_FILE):
    default_config = pd.DataFrame({"key": ["open_times"], "value": ["10:00,11:00,13:00,14:00,15:00,16:00,17:00,18:00,19:00,20:00"]})
    default_config.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, encoding="utf-8-sig").astype(str)
    return pd.DataFrame(columns=COLS)

def get_config():
    conf = pd.read_csv(CONFIG_FILE, encoding="utf-8-sig")
    return conf.loc[conf['key'] == 'open_times', 'value'].values[0].split(',')

# --- 介面開始 ---
st.set_page_config(page_title="專業美容管理系統 v2.1", layout="wide")

df = load_data()
open_times = get_config()

# 側邊欄：切換模式與登入
st.sidebar.title("🎀 選單")
mode = st.sidebar.radio("功能切換", ["👤 客戶線上預約", "🔐 店家管理後台"])

if mode == "👤 客戶線上預約":
    st.header("✨ 美容工作室線上預約")
    st.markdown("---")
    
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("選擇預約日期", min_value=date.today())
            name = st.text_input("客人姓名*")
            line_id = st.text_input("您的 LINE 暱稱*")
        with col2:
            # 過濾已約時段
            booked_times = df[(df["日期"] == str(selected_date)) & (df["狀態"] != "已取消")]["時段"].tolist()
            available_times = [t for t in open_times if t not in booked_times]
            selected_time = st.selectbox("選擇預約時段*", available_times if available_times else ["當日已滿"])
            phone = st.text_input("聯絡電話*")
            referrer = st.text_input("推薦人 (選填)")

        service = st.selectbox("施作項目", ["美甲設計", "美睫嫁接", "護膚SPA", "半永久紋繡", "其他諮詢"])
        note = st.text_area("備註說明 (如有卸甲需求請註明)")
        
        if st.form_submit_button("送出預約"):
            if not (name and phone and line_id) or selected_time == "當日已滿":
                st.error("❌ 請填寫所有必填欄位 (*)，並確認時段是否被選走。")
            else:
                new_row = [str(selected_date), selected_time, name, phone, line_id, service, referrer, "0", "預約中", note]
                new_df = pd.DataFrame([new_row], columns=COLS)
                df = pd.concat([df, new_df], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                
                st.success(f"✅ 預約提交成功！")
                st.balloons()
                st.info(f"💌 為了確保預約成功，請加入我們的 LINE 並告知您的姓名：{name}")
                # 這裡記得換成你真正的 LINE 好友連結
                st.markdown("[👉 點我加入店家 LINE 聯繫確認](https://line.me/ti/p/你的ID)")

else:
    # --- 店家管理後台 ---
    st.header("🔐 店家管理後台")
    pwd = st.sidebar.text_input("後台登入密碼", type="password")
    
    if pwd == ADMIN_PASSWORD:
        tab1, tab2, tab3, tab4 = st.tabs(["📅 月曆檢視", "👥 客戶紀錄彙整", "⚙️ 時段與設定", "📋 訂單編輯管理"])
        
        with tab1:
            st.subheader("本月預約概覽")
            view_date = st.date_input("選擇日期查詢詳情", date.today())
            day_detail = df[df["日期"] == str(view_date)]
            if not day_detail.empty:
                st.table(day_detail[["時段", "客人姓名", "LINE暱稱", "施作項目", "推薦人", "狀態"]])
            else:
                st.write("☕ 這天暫時沒有預約。")

        with tab2:
            st.subheader("👥 客戶消費與推薦紀錄")
            if not df.empty:
                customer_summary = df.groupby(['客人姓名', '電話', 'LINE暱稱']).agg({
                    '日期': 'count',
                    '金額': lambda x: pd.to_numeric(x, errors='coerce').sum(),
                    '推薦人': lambda x: ', '.join(set(x.dropna())) if not x.dropna().empty else "無"
                }).rename(columns={'日期': '總預約次數', '金額': '累計消費額'})
                st.dataframe(customer_summary, use_container_width=True)
            else:
                st.write("尚無客戶資料。")

        with tab3:
            st.subheader("⚙️ 營業時段自定義")
            current_times_str = ",".join(open_times)
            new_times_input = st.text_area("請輸入開放時段 (用半型逗號隔開)", current_times_str)
            if st.button("更新營業時段"):
                conf_df = pd.DataFrame({"key": ["open_times"], "value": [new_times_input]})
                conf_df.to_csv(CONFIG_FILE, index=False, encoding="utf-8-sig")
                st.success("✅ 時段已更新，客戶預約介面將同步顯示新時段。")
                st.rerun()

        with tab4:
            st.subheader("📋 訂單資料管理 (可直接修改內容)")
            # 讓店家可以直接編輯金額與狀態
            df_edit = df.copy()
            updated_df = st.data_editor(df_edit, use_container_width=True, num_rows="dynamic")
            
            if st.button("💾 儲存所有修改"):
                updated_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("✅ 資料庫已成功同步更新！")
                st.rerun()
    
    elif pwd != "":
        st.error("🚫 密碼錯誤，請重新輸入。")
