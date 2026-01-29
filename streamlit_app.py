import streamlit as st
from datetime import datetime, timedelta, timezone
import urllib.parse

# 1. 基本設定 (時區與樣式)
st.set_page_config(page_title="專業預約系統", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FFFBFC; }
    h1 { color: #D44E7D; text-align: center; font-weight: bold; }
    .booking-card { 
        background: white; padding: 30px; border-radius: 20px; 
        border: 2px solid #FF69B4; box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
    }
    .stButton>button { 
        background: linear-gradient(135deg, #FF69B4 0%, #FF1493 100%); 
        color: white; border-radius: 20px; height: 3.5rem; width: 100%; border: none; font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 標題
st.markdown("<h1>🌸 歡迎預約您的美麗時光 🌸</h1>", unsafe_allow_html=True)

# 3. 預約表單內容
with st.container():
    st.markdown("<div class='booking-card'>", unsafe_allow_html=True)
    
    # 日期與時段
    col1, col2 = st.columns(2)
    with col1:
        sel_date = st.date_input("📅 選擇日期", datetime.now().date())
    with col2:
        sel_time = st.selectbox("🕒 選擇時段", ["14:00", "16:00", "18:00"])

    st.divider()
    
    # 客人基本資料
    c1, c2 = st.columns(2)
    name = c1.text_input("客人姓名*")
    line_n = c2.text_input("LINE 暱稱*")
    
    phone = st.text_input("手機號碼*")
    
    # 服務項目
    items = st.multiselect("🛠️ 施作項目 (可多選)*", ["手部美甲", "足部保養", "睫毛嫁接", "霧眉設計"])
    
    st.divider()

    # 送出按鈕
    if st.button("🚀 整理預約資料"):
        if name and line_n and phone and items:
            # 整理預約訊息文字
            summary_msg = (
                f"【新預約申請】\n"
                f"📅 日期：{sel_date}\n"
                f"🕒 時段：{sel_time}\n"
                f"👤 姓名：{name}\n"
                f"🆔 LINE：{line_n}\n"
                f"📱 電話：{phone}\n"
                f"🛠️ 項目：{', '.join(items)}"
            )
            
            st.success("✅ 資料已整理完成！")
            st.balloons()
            
            # 顯示整理好的資料，方便複製
            st.code(summary_msg)
            
            # 製作 LINE 傳送連結
            line_url = f"https://line.me/R/msg/text/?{urllib.parse.quote(summary_msg)}"
            
            # 製作 Google 日曆 預存連結 (讓你點了之後手動存入)
            start_dt = f"{str(sel_date).replace('-', '')}T{sel_time.replace(':', '')}00"
            end_hour = int(sel_time.split(':')[0]) + 2
            end_dt = f"{str(sel_date).replace('-', '')}T{end_hour:02}0000"
            gcal_url = f"https://www.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote('預約:'+name)}&dates={start_dt}/{end_dt}&details={urllib.parse.quote(summary_msg)}&sf=true&output=xml"

            # 提供兩個選項給店家/客人
            st.markdown(f"""
                <a href="{line_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#00B900;color:white;padding:12px;text-align:center;border-radius:10px;margin-bottom:10px;font-weight:bold;">
                        💬 透過 LINE 傳送預約給店家
                    </div>
                </a>
                <a href="{gcal_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#4285F4;color:white;padding:12px;text-align:center;border-radius:10px;font-weight:bold;">
                        📅 將預約加入我的 Google 日曆
                    </div>
                </a>
            """, unsafe_allow_html=True)
            
        else:
            st.error("❌ 請填寫姓名、LINE、手機與施作項目。")

    st.markdown("</div>", unsafe_allow_html=True)

# 側邊欄
st.sidebar.markdown("### 🔔 使用小秘訣")
st.sidebar.info("填寫完畢後點擊按鈕，您可以選擇傳送 LINE 給老師，或直接存入您的日曆備忘喔！")
