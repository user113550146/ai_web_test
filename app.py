import os
import streamlit as st
from google import genai
from dotenv import load_dotenv
import chat
import model_setting
import tools  # 新增導入


user_ava="🟦"
ai_ava="⚫"
# 1. 讀取環境變數
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 初始化 tools session state (確保 tools 列表在 session 中保存)
if "tools_list" not in st.session_state:
    tools.reset_tools()

# 初始化 genai client
if "genai_client" not in st.session_state:
    st.session_state.genai_client = genai.Client(api_key=api_key)


# 2. 頁面基本設定
#####頁面設定#####
st.set_page_config(page_title="title", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 20px; /* 設定你想要的基礎大小 */
    }
    .stChatMessage {
        background-color: #eaf700 !important;
    }
    .stTextInput-RootElement {
        background-color: #eaf700 !important;
    }
    input {
        background-color: #eaf700 !important;
    }
    .stTextArea {
        background-color: #eaf700 !important;
    }
    textarea {
        background-color: #eaf700 !important;
    }
    .stAlertContentWarning{
        font-color: #eaf700
            }
    </style>
    """, unsafe_allow_html=True)





# --- 預設參數 (不對使用者開放) ---
temp = 0.5
top = 0.85
tok = 18
mtk = 2048
stream = False
user_system_prompt = "你是一個專業的繁體中文助手。"
rag_enabled = True
rag_depth = 3

# --- 側邊欄 ---
with st.sidebar:
    st.title("設定")
    
    #st.subheader("多模態設定")
    input_mode = st.radio("輸入格式", ["文字", "圖片"], key='input_mode', horizontal=True, on_change=chat.rst)
    output_mode = st.radio("預期輸出", ["文字", "圖片"], key='output_mode', horizontal=True, on_change=chat.rst)
    
    # 根據輸出模式選擇模型
    if output_mode == "圖片":
        choice = 'gemini-2.5-flash-image'
    else:
        choice = 'gemini-2.5-flash'
        
    st.divider()
    if st.button("清空對話", use_container_width=True):
        st.success("對話已清空！")
        chat.rst()
        st.rerun()
    
#####model setting#####
# 初始化模型配置
model_config = model_setting.get_model_config(temperature=temp, top_p=top, top_k=tok, max_output_tokens=mtk, user_system_prompt=user_system_prompt, output_mode=output_mode)

# 调用聊天界面
chat.chat_interface(st.session_state.genai_client, choice, model_config, user_ava, ai_ava, stream, input_mode, rag_enabled, rag_depth)
