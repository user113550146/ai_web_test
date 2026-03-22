import streamlit as st
import time
import re

def sanitize_input(text, max_length=2000):
    """
    清理用户输入，防止注入攻击
    """
    if not text:
        return ""

    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 移除JavaScript代码
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

    # 移除潜在的系统命令
    dangerous_patterns = [
        r'system\(', r'exec\(', r'eval\(', r'import os', r'import subprocess',
        r'os\.', r'subprocess\.', r'__import__', r'open\(', r'file\('
    ]
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE)

    # 限制长度
    return text[:max_length]

def log_security_event(event_type, details):
    """
    记录安全事件（可扩展为写入文件或发送警报）
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    event = f"[{timestamp}] SECURITY: {event_type} - {details}"
    print(event)  # 在生产环境中应该写入安全日志文件
def leave():
    """
    當使用者輸入'離開'時呼叫這個函數
    """
    #print("leave")
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmd = str(proc.info['cmdline'])
        if 'streamlit' in cmd:
            proc.terminate()
    return

def happy():
    """
    當使用者開心的時候呼叫這個function
    """
    st.balloons()
    return

def never_gonna_give_you_up(ai_response=None):
    """
    或者使用者輸入'rickroll'的時候呼叫
    或者使用者輸入' 來部影片' 的時候呼叫
    """
    # """
    # 執行狀態會被保存在 session_state 中，頁面重新加載時會保留結果

    # 參數:
    #     ai_response: AI的回复內容，如果提供會一同保存到歷史記錄
    # """
    RICKROLL_URL = "https://youtu.be/dQw4w9WgXcQ?si=gnR0ti0GfmT9nSeu"
    
    # 初始化狀態
    if "rickroll_played" not in st.session_state:
        st.session_state.rickroll_played = False
        st.session_state.rickroll_timestamp = None
    
    # 標記視頻已被播放
    st.session_state.rickroll_played = True
    st.session_state.rickroll_timestamp = str(st.session_state.get("current_time", ""))
    
    # 顯示視頻
    st.video(data=RICKROLL_URL)

    # 將視頻和AI回复保存到聊天歷史記錄
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 檢查最後一條消息是否已是視頻記錄（避免重複保存）
    is_already_saved = False
    if st.session_state.chat_history:
        last_message = st.session_state.chat_history[-1]
        if (last_message.get("role") == "system" and
            "type" in last_message and
            last_message["type"] == "video" and
            RICKROLL_URL in last_message.get("video_url", "")):
            is_already_saved = True

    if not is_already_saved:
        # 如果有AI回复，一起保存
        if ai_response:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": ai_response
            })

        st.session_state.chat_history.append({
            "role": "system",
            "type": "video",
            "content": f"",
            "video_url": RICKROLL_URL
        })

    # 顯示執行狀態指示
    # col1, col2 = st.columns(2)
    # with col1:
    #     st.success("✅ 視頻播放已保存到會話中")
    # with col2:
    #     if st.button("重置視頻狀態"):
    #         st.session_state.rickroll_played = False
    #         st.session_state.rickroll_timestamp = None
    #         # 從歷史記錄中移除視頻記錄和相關的AI回复
    #         filtered_history = []
    #         skip_next = False
    #         for msg in st.session_state.chat_history:
    #             if skip_next:
    #                 skip_next = False
    #                 continue
    #             if (msg.get("type") == "video" and RICKROLL_URL in msg.get("video_url", "")):
    #                 skip_next = True  # 跳過下一個消息（通常是視頻消息之前的AI回复）
    #                 continue
    #             filtered_history.append(msg)
    #         st.session_state.chat_history = filtered_history
    #         st.rerun()
    return

def _sleep(sleep_time=10.0):
    """
    當使用者輸入'sleep' 或'睡'時呼叫,必須等待return 
    """
    try:
        if not(sleep_time>0 and sleep_time<60):
            sleep_time=10.0
    except :
        sleep_time=10.0
    time.sleep(sleep_time)
    return None
# 預設工具列表
_default_tools = [ happy, never_gonna_give_you_up,_sleep]

def get_tools():
    """
    從 session_state 獲取工具列表，確保跨 Streamlit rerun 時保存
    """
    if "tools_list" not in st.session_state:
        st.session_state.tools_list = _default_tools.copy()
    return st.session_state.tools_list

def reset_tools():
    """
    重置工具列表為預設值
    """
    st.session_state.tools_list = _default_tools.copy()

def add_tool(tool_func):
    """
    添加新工具函數到工具列表
    """
    tools_list = get_tools()
    if tool_func not in tools_list:
        tools_list.append(tool_func)
        st.session_state.tools_list = tools_list

def remove_tool(tool_func):
    """
    從工具列表移除工具函數
    """
    tools_list = get_tools()
    if tool_func in tools_list:
        tools_list.remove(tool_func)
        st.session_state.tools_list = tools_list

# 提供一個類似原始變量的訪問方式
@property
def _tools_property():
    return get_tools()

# 使用一個自訂類來支援模組級別的動態訪問
class _ToolsModule:
    def __getattr__(self, name):
        if name == 'tools':
            return get_tools()
        raise AttributeError(f"Module 'tools' has no attribute '{name}'")