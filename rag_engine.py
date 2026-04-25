import os
import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv

# 確保載入環境變數
load_dotenv()

# 嘗試載入 Weaviate 模組，如果沒有安裝也能正常執行其他功能
try:
    import weaviate
    from weaviate.classes.init import Auth
    import weaviate.classes.config as wvc_config
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

@st.cache_resource
def get_weaviate_client():
    if not WEAVIATE_AVAILABLE:
        return None
    url = os.getenv("WEAVIATE_URL")
    api_key = os.getenv("WEAVIATE_API_KEY")
    if not url or not api_key:
        return None
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
        )
        return client
    except Exception as e:
        error_msg = f"Weaviate 連線失敗: {e}"
        print(error_msg)
        st.error(error_msg)
        return None

def init_collection():
    """初始化 ChatMemory 集合 (Collection)"""
    client = get_weaviate_client()
    if not client: 
        return
    try:
        if not client.collections.exists("ChatMemory"):
            # 建立集合並設定屬性
            client.collections.create(
                name="ChatMemory",
                properties=[
                    wvc_config.Property(name="user_query", data_type=wvc_config.DataType.TEXT),
                    wvc_config.Property(name="ai_response", data_type=wvc_config.DataType.TEXT),
                    wvc_config.Property(name="timestamp", data_type=wvc_config.DataType.DATE),
                ]
            )
            print("ChatMemory Collection 已成功建立。")
    except Exception as e:
        error_msg = f"Collection 初始化失敗: {e}"
        print(error_msg)
        st.error(error_msg)

def retrieve_context(query, limit=3):
    """
    RAG 檢索：根據使用者問題尋找相關的歷史記憶
    """
    # 確保傳入的 query 是文字，如果是圖片等多模態列表則取第一項文字
    text_query = query[0] if isinstance(query, list) else str(query)
    
    client = get_weaviate_client()
    if not client: 
        return ""
    try:
        # 確保 Collection 存在
        init_collection()
        
        collection = client.collections.get("ChatMemory")
        
        # 嘗試 BM25 關鍵字搜尋
        response = collection.query.bm25(
            query=text_query,
            query_properties=["user_query", "ai_response"],
            limit=limit
        )
        
        context = ""
        if response.objects:
            print(f"BM25 檢索成功，找到 {len(response.objects)} 筆相關記憶。")
            for obj in response.objects:
                q = obj.properties.get('user_query', '')
                a = obj.properties.get('ai_response', '')
                context += f"User: {q}\nAI: {a}\n\n"
        else:
            # 如果 BM25 沒找到，回退到獲取最近的記憶 (至少提供一些上下文)
            print(f"BM25 未找到相關記憶，回退到最近記憶。")
            recent_resp = collection.query.fetch_objects(limit=limit)
            if recent_resp.objects:
                for obj in recent_resp.objects:
                    q = obj.properties.get('user_query', '')
                    a = obj.properties.get('ai_response', '')
                    context += f"User: {q}\nAI: {a}\n\n"
            
        return context.strip()
    except Exception as e:
        error_msg = f"檢索記憶失敗: {e}"
        print(error_msg)
        st.error(error_msg)
        return ""

def save_memory(query, response):
    """
    儲存新的對話到 Weaviate 向量資料庫
    """
    # 確保傳入的 query 是文字，如果是列表則取第一項
    text_query = query[0] if isinstance(query, list) else str(query)
    
    # 如果 query 包含 RAG 標籤，則過濾掉 context 只取當前問題
    if "【當前問題】" in text_query:
        text_query = text_query.split("【當前問題】")[-1].strip()
    
    client = get_weaviate_client()
    if not client: 
        return
    try:
        # 確保 Collection 已初始化
        init_collection()
        
        collection = client.collections.get("ChatMemory")
        collection.data.insert({
            "user_query": text_query,
            "ai_response": str(response),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(f"已儲存對話到 RAG: {text_query[:20]}...")
    except Exception as e:
        error_msg = f"儲存記憶失敗: {e}"
        print(error_msg)
        st.error(error_msg)

def clear_memory():
    """
    刪除 Weaviate 中的 ChatMemory 集合以清除所有歷史記憶
    """
    client = get_weaviate_client()
    if not client:
        return False
    try:
        if client.collections.exists("ChatMemory"):
            client.collections.delete("ChatMemory")
            # 重新初始化空的集合
            init_collection()
        return True
    except Exception as e:
        error_msg = f"清除記憶失敗: {e}"
        print(error_msg)
        st.error(error_msg)
        return False
