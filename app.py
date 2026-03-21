import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import chat
import model_setting
import tools  # 新增導入


user_ava="🟦"
ai_ava="⚫"
# 1. 讀取環境變數
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 初始化 tools session state (確保 tools 列表在 session 中保存)
if "tools_list" not in st.session_state:
    tools.reset_tools()




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





llmlist=['gemini-3.1-flash-lite-preview','gemini-3-flash-preview']
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# --- 側邊欄：自訂 System Prompt ---
with st.sidebar:
    st.title("設定")
    choice=st.radio("模型",
                    llmlist,
                    key='model_sel',
                    on_change=chat.rst,)
    temp=st.slider(label="temperature",min_value=.0,max_value=1.5,value=0.5,step=0.05,format="%.2f")
    top=st.slider(label="top_p",min_value=.0,max_value=1.0,value=0.85,step=0.05,format="%.2f")
    tok=st.slider(label="top_k",min_value=1,max_value=35,value=18,step=1,format="%d")
    mtk=st.slider(label="max_output_token",min_value=1,max_value=8192,value=2048,step=1,format="%d")
    #web_content_url = st.text_input("參考網頁 URL (選填)")
    #thought=st.checkbox(label="是否輸出思考過程",value=False,help="啟用後模型將在回應中包含思考過程的內容，適合需要分析推理的問題。")
    stream=st.checkbox(label="streaming",value=True,on_change=chat.rst)
    # 使用 text_area 讓使用者輸入長文本
    if choice in ['gemini-3.1-flash-lite-preview','gemini-3-flash-preview'] :
        user_system_prompt = st.text_area(
            "System Prompt:",
            value="你是一個不專業的繁體中文助手，請用毫不相干的話回答問題。",
            height=200,
            help="在這裡輸入你希望 AI 扮演的角色，例如：'你是一個AI'"
        )
        #st.info("更換 System Prompt 後建議清空對話")
    else :
        user_system_prompt =""
    # 提供一個重置按鈕，因為更換角色通常需要清空記憶
    # c1,c2=st.columns(2)
    # with c1:
    #     if st.button("更新設定"):
    #         #st.session_state.chat_history = []
    #         st.success("設定已更新！")
    #         st.rerun()
    # with c2:
    #     if st.button("清空對話"):
    #         #st.success("設定已更新！")
    #         rstres=chat.rst()
    #         if(rstres!=None):
    #             print(rstres)
    #         st.rerun()
    # st.divider()
    if st.button("更新設定並清空對話"):
        st.success("設定已更新！")
        rstres=chat.rst()
        if(rstres!=None):
            print(rstres)
        st.rerun()
    
#####model setting#####
model= model_setting.initialize_gemini_model(model_name=choice, temperature=temp, top_p=top, top_k=tok, max_output_tokens=mtk, user_system_prompt=user_system_prompt)
# 调用聊天界面
chat.chat_interface(model, user_ava, ai_ava,stream)