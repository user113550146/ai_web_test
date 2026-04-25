import streamlit as st
from google.genai import types
import re
import tools

# --- 功能 2：根據選擇獲取模型配置 ---
def get_model_config(temperature, top_p, top_k, max_output_tokens, user_system_prompt, output_mode="文字"):
    # 验证和清理用户输入的系统提示词
    if user_system_prompt:
        # 移除潜在的危险字符
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

    # 构建完整指令
    base_instruction = "請使用中文回應。如果有合適的工具優先考慮使用工具回答。"

    # 如果是圖片模式，我們不需要 Pollinations 的指令了，因為將使用原生生成
    if output_mode == "圖片":
        base_instruction += "\n\n【重要指示】使用者要求生成圖片。請根據使用者的描述生成一張高品質的圖片。如果是連續對話，請根據先前的圖片內容進行修改或延續。"

    if user_system_prompt and user_system_prompt.strip():
        full_instruction = base_instruction + "\n" + user_system_prompt
    else:
        full_instruction = base_instruction

    # 建立 GenerateContentConfig
    config_params = {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
        "system_instruction": full_instruction,
    }

    # 📌 關鍵修改：如果輸出模式是圖片，加入 response_modalities
    if output_mode == "圖片":
        config_params["response_modalities"] = ["IMAGE"]
        config_params["image_config"] = types.ImageConfig(
            aspect_ratio="1:1",
            image_size="1K"
        )
    else:
        config_params["response_modalities"] = ["TEXT"]
        config_params["tools"] = tools.get_tools() # 僅在文字模式下加入工具列表

    return types.GenerateContentConfig(**config_params)

