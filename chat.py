
# 聊天界面相关的函数模块

import streamlit as st

def rst():
    # 重置聊天会话
    try:
        st.session_state.chat_history = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        return None
    except Exception as e:
        return e


def init_chat_session(model,stream):
    # 初始化聊天会话，使用 model.start_chat()
    # 如果 stream 设置改变了，则重新初始化聊天会话
    
    should_reinit = False
    
    # 检查是否需要初始化
    if "chat_session" not in st.session_state:
        should_reinit = True
    # 检查 stream 设置是否改变
    elif "last_stream_setting" not in st.session_state:
        should_reinit = True
    elif st.session_state.get("last_stream_setting") != stream:
        should_reinit = True
    
    if should_reinit:
        # 创建新的聊天会话，初始历史为空
        if not stream:
            st.session_state.chat_session = model.start_chat(history=[],enable_automatic_function_calling=True)
        else:
            st.session_state.chat_session = model.start_chat(history=[],enable_automatic_function_calling=False)

        st.session_state.chat_history = []
        # 保存当前的 stream 设置
        st.session_state.last_stream_setting = stream


def display_chat_history(user_ava, ai_ava):
    # 显示历史对话记录
    for message in st.session_state.chat_history:
        role = message["role"]
        
        # 特殊处理視頻類型的消息
        if message.get("type") == "video" and "video_url" in message:
            with st.chat_message("assistant", avatar=ai_ava):
                st.markdown(message.get("content", "🎬 視頻"))
                st.video(data=message["video_url"])
        else:
            # 常规文本消息处理
            avatar = user_ava if role == "user" else ai_ava
            with st.chat_message(role, avatar=avatar):
                st.markdown(message["content"])


def add_user_message_to_history(prompt, user_ava):
    # 清理用户输入，防止XSS
    import re
    if prompt:
        # 移除HTML标签和JavaScript
        prompt = re.sub(r'<[^>]+>', '', prompt)
        prompt = re.sub(r'javascript:', '', prompt, flags=re.IGNORECASE)
        prompt = re.sub(r'on\w+\s*=', '', prompt, flags=re.IGNORECASE)
        # 限制长度
        prompt = prompt[:2000]

    with st.chat_message("user", avatar=user_ava):
        st.write(prompt)
    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })


def display_ai_response_stream(chat_session, prompt, ai_ava,stream):
    
    # 通过流式或非流式输出显示 AI 回应，并保存到历史记录
    
    # 参数:
    #     chat_session: Gemini 聊天会话实例
    #     prompt: 用户的问题
    #     ai_ava: AI 头像
    #     stream: 是否使用流式模式
    
    # 返回:
    #     bool: 是否成功获取回应
   
    with st.chat_message("assistant", avatar=ai_ava):
        response_placeholder = st.empty()
        full_response = ""
        content_received = False
        try:
            # 根据 stream 模式选择不同的发送方式
            if stream:
                # 流式模式
                response = chat_session.send_message(prompt, stream=True)
            else:
                # 非流式模式，使用字典方式配置 tool_config
                tool_config = {
                    "function_calling_config": {
                        "mode": "AUTO"
                    }
                }
                response = chat_session.send_message(prompt, stream=False, tool_config=tool_config)
            # 逐块处理响应
            for chunk in response:
                try:
                    if chunk.text:
                        content_received = True
                        full_response += chunk.text
                        # 实时更新显示 (加上游标感)
                        if stream:
                            response_placeholder.write(full_response + "▌")
                except (ValueError, IndexError):
                    # chunk.text 被攔截时继续处理下一块
                    continue

            # 响应完成后的处理
            if content_received:
                # 清理AI回复内容
                import re
                full_response = re.sub(r'<script[^>]*>.*?</script>', '', full_response, flags=re.IGNORECASE | re.DOTALL)
                full_response = re.sub(r'javascript:', '', full_response, flags=re.IGNORECASE)
                full_response = full_response[:10000]  # 限制长度

                # 移除游标，显示最终完整内容
                response_placeholder.write(full_response)
                # 保存到历史记录
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response
                })

                # 检查是否有工具调用
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'function_calls') and candidate.function_calls:
                        for function_call in candidate.function_calls:
                            # 获取工具函数
                            tool_name = function_call.name
                            tool_args = function_call.args if hasattr(function_call, 'args') else {}

                            # 动态导入并调用工具函数
                            try:
                                import tools
                                if hasattr(tools, tool_name):
                                    tool_func = getattr(tools, tool_name)
                                    # 传递AI回复内容给工具函数
                                    tool_func(ai_response=full_response, **tool_args)
                            except Exception as e:
                                st.error(f"工具调用错误: {e}")

                return True
            else:
                # 整个流程完成但没有获取到内容 - 通常是安全过滤器拦截
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    reason = candidate.finish_reason
                    
                    # 列出可能的原因代码
                    reason_map = {
                        0: "未指定原因",
                        1: "STOP - 模型正常停止",
                        2: "MAX_TOKENS - 达到最大 token 数",
                        3: "SAFETY - 被安全政策拦截",
                        4: "RECITATION - 涉及过多引述内容"
                    }
                    
                    reason_text = reason_map.get(reason, f"未知原因代码: {reason}")
                    
                    st.warning(
                        f"⚠️ 回应未产出\n\n"
                        f"**原因**: {reason_text}\n\n"
                        "**建议**:\n"
                        "- 尝试换个更具体的问题\n"
                        "- 避免敏感或有争议的话题\n"
                        "- 检查 System Prompt 是否过于激进"
                    )
                else:
                    st.error("❌ 无法获取模型回应，请稍后重试。")
                return False

        except Exception as e:
            error_str = str(e).lower()
            # 檢查是否為配額超限錯誤（429）
            if "429" in error_str or "quota" in error_str or "exceeded" in error_str:
                st.error(
                    "❌ **API 配額已用完**\n\n"
                    "免費層已達今日使用限制。解決方案：\n"
                    "1. **等待 24 小時** - 配額會在午夜 UTC 時重置\n"
                    "2. **升級計畫** - 查看 Google AI Studio 升級到付費版本\n"
                    "3. **稍後重試** - 等待一段時間後重試\n\n"
                    f"詳情: {e}"
                )
            else:
                st.error(f"API 连接或其他错误: {e}")
            return False


def chat_interface(model, user_ava, ai_ava,stream):
    
    # 主聊天界面逻辑
    # 使用 model.start_chat() 方式管理聊天会话
    
    # 参数:
    #     model: Gemini 模型实例
    #     user_ava: 用户头像
    #     ai_ava: AI 头像
   
    # 初始化聊天会话
    init_chat_session(model,stream)

    # 显示历史对话
    display_chat_history(user_ava, ai_ava)

    # 处理用户输入
    if prompt := st.chat_input("你有什麽問題?"):
        # 显示用户消息
        add_user_message_to_history(prompt, user_ava)

        # 调用聊天会话并显示流式响应
        display_ai_response_stream(st.session_state.chat_session, prompt, ai_ava,stream=stream)
