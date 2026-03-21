import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import tools
# def get_web_content(url):
#     if not url:
#         return ""
#     # 验证URL格式，防止恶意URL
#     import re
#     if not re.match(r'^https?://', url):
#         st.error("URL必須以http://或https://開頭")
#         return ""
#     if len(url) > 2000:  # 限制URL長度
#         st.error("URL太長")
#         return ""
#     try:
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()
#         response.encoding = 'utf-8'
#         soup = BeautifulSoup(response.text, 'html.parser')
#         # 移除腳本與樣式，只取文字
#         for script in soup(["script", "style"]):
#             script.extract()
#         return soup.get_text(separator="\n", strip=True)[:5000] # 限制長度避免 Token 爆炸
#     except Exception as e:
#         st.error(f"網址讀取失敗: {e}")
#         return ""

# --- 功能 2：根據選擇初始化模型 ---
def initialize_gemini_model(model_name, temperature, top_p, top_k, max_output_tokens, user_system_prompt):
    # 验证和清理用户输入的系统提示词
    if user_system_prompt:
        # 移除潜在的危险字符
        import re
        user_system_prompt = re.sub(r'[<>]', '', user_system_prompt)  # 移除尖括号
        user_system_prompt = user_system_prompt[:2000]  # 限制长度
        # 确保不包含系统命令
        dangerous_patterns = [
            r'system\(', r'exec\(', r'eval\(', r'import os', r'import subprocess',
            r'os\.', r'subprocess\.', r'__import__', r'open\(', r'file\('
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, user_system_prompt, re.IGNORECASE):
                st.warning("系統提示詞包含潛在危險內容，已被過濾")
                user_system_prompt = re.sub(pattern, '[FILTERED]', user_system_prompt, flags=re.IGNORECASE)

    # 限制 max_output_tokens 以節省配額
    max_output_tokens = max_output_tokens
    web_content=False
    # 构建完整指令，确保 System Prompt 不会互相冲突
    base_instruction = "請使用中文回應。不要輸出markdown.如果有合適的tools優先考慮使用tool回答."
    if user_system_prompt and user_system_prompt.strip():
        full_instruction = base_instruction + "\n" + user_system_prompt
    else:
        full_instruction = base_instruction
    
    if web_content:
        # 進一步限制網頁內容，減少 token 消耗
        if len(web_content) > 1024:
            web_content = web_content[:1024] + "..."
        full_instruction += f"\n\n【參考資料】\n{web_content}"
    
    # 改进安全设置：平衡安全性和实用性
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        #HarmCategory.HARM_CATEGORY_UNSPECIFIED:HarmBlockThreshold.BLOCK_NONE
}
    # 初始化模型
    generation_config_dict = {
        "temperature":temperature,
        "top_p":top_p,
        "top_k":top_k,
        "max_output_tokens":max_output_tokens
    }
    
    model = genai.GenerativeModel(
    model_name=model_name,
    system_instruction=full_instruction,
    generation_config=generation_config_dict,
    safety_settings=safety_settings,
    tools=tools.get_tools()
)
    return model