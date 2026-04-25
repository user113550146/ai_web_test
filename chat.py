
# 聊天界面相关的函数模块

import streamlit as st
import rag_engine
from google.genai import types
from PIL import Image
import io

def rst():
    # 重置聊天会话
    try:
        st.session_state.chat_history = []
        if "chat_session" in st.session_state:
            del st.session_state["chat_session"]
        return None
    except Exception as e:
        return e


def init_chat_session(client, model_id, config, stream):
    # 初始化聊天会话
    
    should_reinit = False
    
    # 检查是否需要初始化
    if "chat_session" not in st.session_state:
        should_reinit = True
    # 检查 stream 设置是否改变
    elif "last_stream_setting" not in st.session_state:
        should_reinit = True
    elif st.session_state.get("last_stream_setting") != stream:
        should_reinit = True
    # 檢查模型或配置是否改變
    elif st.session_state.get("last_model_id") != model_id:
        should_reinit = True
    
    if should_reinit:
        # 使用新的 SDK 初始化對話
        st.session_state.chat_session = client.chats.create(
            model=model_id,
            config=config,
            history=[]
        )
        st.session_state.chat_history = []
        st.session_state.last_stream_setting = stream
        st.session_state.last_model_id = model_id


def display_chat_history(user_ava, ai_ava):
    # 显示历史对话记录
    for message in st.session_state.chat_history:
        role = message["role"]
        
        # 特殊处理視頻類型的消息
        if message.get("type") == "video" and "video_url" in message:
            with st.chat_message("assistant", avatar=ai_ava):
                st.markdown(message.get("content", "🎬 視頻"))
                st.video(data=message["video_url"])
        elif message.get("type") == "image":
            # 渲染圖片歷史記錄
            with st.chat_message(role, avatar=user_ava if role == "user" else ai_ava):
                if "image_data" in message:
                    st.image(message["image_data"], caption=message.get("content", ""))
                elif "image_url" in message:
                    st.image(message["image_url"], caption=message.get("content", ""))
                
                content = message.get("content", "")
                if content:
                    st.markdown(content)
        else:
            # 常规文本消息处理
            avatar = user_ava if role == "user" else ai_ava
            with st.chat_message(role, avatar=avatar):
                st.markdown(message["content"])


def add_user_message_to_history(prompt, user_ava, image_data=None):
    # 清理用户输入
    import re
    if prompt:
        prompt = re.sub(r'<[^>]+>', '', prompt)
        prompt = prompt[:2000]

    with st.chat_message("user", avatar=user_ava):
        if image_data:
            st.image(image_data, caption=prompt)
        else:
            st.write(prompt)
            
    if image_data:
        st.session_state.chat_history.append({
            "role": "user",
            "type": "image",
            "image_data": image_data,
            "content": prompt
        })
    else:
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt
        })
    return prompt


def display_ai_response_stream(chat_session, prompt_or_list, ai_ava, stream, original_query=None):
    
    with st.chat_message("assistant", avatar=ai_ava):
        response_placeholder = st.empty()
        full_response_text = ""
        generated_images = []
        content_received = False
        
        try:
            if stream:
                # 流式模式
                response_stream = chat_session.send_message_stream(prompt_or_list)
                if response_stream:
                    for chunk in response_stream:
                        content_received = True
                        # 處理 chunk
                        if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                            for part in chunk.candidates[0].content.parts:
                                if part.text:
                                    full_response_text += part.text
                                    response_placeholder.write(full_response_text + "▌")
                                if part.inline_data:
                                    # 修正：SDK 可能返回 types.Image 而非 PIL Image
                                    res = part.as_image()
                                    img = res._pil_image if hasattr(res, '_pil_image') else res
                                    
                                    # 安全地設置 format 屬性（僅針對 PIL Image）
                                    if hasattr(img, 'format') and not getattr(img, 'format', None):
                                        try:
                                            img.format = "PNG"
                                        except:
                                            pass
                                    generated_images.append(img)
            else:
                # 非流式模式
                response = chat_session.send_message(prompt_or_list)
                if response:
                    content_received = True
                    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.text:
                                full_response_text += part.text
                            if part.inline_data:
                                # 修正：SDK 可能返回 types.Image 而非 PIL Image
                                res = part.as_image()
                                img = res._pil_image if hasattr(res, '_pil_image') else res
                                
                                # 安全地設置 format 屬性（僅針對 PIL Image）
                                if hasattr(img, 'format') and not getattr(img, 'format', None):
                                    try:
                                        img.format = "PNG"
                                    except:
                                        pass
                                generated_images.append(img)
                
                response_placeholder.write(full_response_text)

            # 响应完成后的处理
            if content_received:
                # 顯示所有生成的圖片
                if generated_images:
                    response_placeholder.empty()
                    for img in generated_images:
                        st.image(img)
                    if full_response_text:
                        st.markdown(full_response_text)
                    
                    # 保存到歷史記錄
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "type": "image",
                        "image_data": generated_images[0],
                        "content": full_response_text
                    })
                else:
                    response_placeholder.write(full_response_text)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": full_response_text
                    })

                # RAG 記憶儲存 (使用原始查詢)
                save_query = original_query if original_query is not None else prompt_or_list
                rag_engine.save_memory(save_query, full_response_text)
                return True
            else:
                st.error("❌ 無法獲取模型回應。")
                return False

        except Exception as e:
            st.error(f"API 連接或其他錯誤: {e}")
            return False


def chat_interface(client, model_id, config, user_ava, ai_ava, stream, input_mode="文字", rag_enabled=True, rag_depth=3):
    
    # 初始化聊天会话
    init_chat_session(client, model_id, config, stream)

    # 显示历史对话
    display_chat_history(user_ava, ai_ava)

    prompt = None
    image_data = None
    
    if input_mode == "文字":
        prompt = st.chat_input("你有什麼問題?")
    else:
        with st.container():
            st.info("請上傳圖片，您可以附加文字說明一起送出給 AI。")
            uploaded_file = st.file_uploader("選擇圖片...", type=["jpg", "jpeg", "png", "webp"])
            text_input = st.text_input("圖片說明 (選填)")
            
            if st.button("送出圖片") and uploaded_file is not None:
                from PIL import Image
                try:
                    image_data = Image.open(uploaded_file)
                    prompt = text_input if text_input else "請描述這張圖片"
                except Exception as e:
                    st.error(f"讀取圖片失敗: {e}")

    if prompt is not None or image_data is not None:
        
        safe_prompt = add_user_message_to_history(prompt, user_ava, image_data)

        # RAG 檢索
        final_prompt = safe_prompt
        original_query = safe_prompt
        if image_data:
            original_query = [safe_prompt, image_data]

        if rag_enabled:
            retrieved_context = rag_engine.retrieve_context(safe_prompt, limit=rag_depth)
            if retrieved_context:
                final_prompt = f"【以下是先前的相關對話脈絡提供參考】\n{retrieved_context}\n\n【當前問題】\n{safe_prompt}"

        if image_data:
            content_to_send = [final_prompt, image_data]
        else:
            content_to_send = final_prompt

        # 调用聊天会话
        display_ai_response_stream(st.session_state.chat_session, content_to_send, ai_ava, stream=stream, original_query=original_query)
