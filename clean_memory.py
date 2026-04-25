import os
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def get_weaviate_client():
    url = os.getenv("WEAVIATE_URL")
    api_key = os.getenv("WEAVIATE_API_KEY")
    if not url or not api_key:
        print("錯誤: 找不到 WEAVIATE_URL 或 WEAVIATE_API_KEY 環境變數。")
        return None
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
        )
        return client
    except Exception as e:
        print(f"Weaviate 連線失敗: {e}")
        return None

def clear_memory():
    """
    刪除 Weaviate 中的 ChatMemory 集合以清除所有歷史記憶
    """
    client = get_weaviate_client()
    if not client:
        return False
    try:
        print("正在檢查並清除 ChatMemory 集合...")
        if client.collections.exists("ChatMemory"):
            client.collections.delete("ChatMemory")
            print("ChatMemory 集合已成功刪除。")
            
            # 重新建立結構 (選用，通常由應用程式啟動時處理)
            import weaviate.classes.config as wvc_config
            client.collections.create(
                name="ChatMemory",
                properties=[
                    wvc_config.Property(name="user_query", data_type=wvc_config.DataType.TEXT),
                    wvc_config.Property(name="ai_response", data_type=wvc_config.DataType.TEXT),
                    wvc_config.Property(name="timestamp", data_type=wvc_config.DataType.DATE),
                ]
            )
            print("ChatMemory 集合已重新初始化。")
        else:
            print("ChatMemory 集合不存在，無需清除。")
        
        client.close()
        return True
    except Exception as e:
        print(f"清除記憶失敗: {e}")
        if client:
            client.close()
        return False

if __name__ == "__main__":
    if clear_memory():
        print("清理程序執行完畢。")
    else:
        print("清理程序執行失敗。")
