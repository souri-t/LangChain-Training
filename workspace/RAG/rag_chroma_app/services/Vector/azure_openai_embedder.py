"""
Azure OpenAI埋め込みクライアント
"""

from typing import List
import requests
from .base_embedder import BaseEmbedder


class AzureOpenAIEmbedder(BaseEmbedder):
    """
    Azure OpenAI API を使ってテキストをベクトル化するクラス。
    
    Azure OpenAI Service のデプロイメントエンドポイントを使用します。
    """

    def __init__(self, api_key: str, endpoint: str, deployment_name: str, api_version: str = "2024-02-01"):
        """
        AzureOpenAIEmbedderの初期化。
        
        Args:
            api_key (str): Azure OpenAI APIキー
            endpoint (str): Azure OpenAIエンドポイントURL（例: https://your-resource.openai.azure.com）
            deployment_name (str): デプロイメント名（例: text-embedding-ada-002）
            api_version (str): APIバージョン（デフォルト: 2024-02-01）
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        # Azure OpenAI Embeddings エンドポイントURL
        self.embeddings_url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/embeddings?api-version={self.api_version}"

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        テキストリストをAzure OpenAI APIでベクトル化する。
        
        Args:
            texts (List[str]): ベクトル化するテキストのリスト
            
        Returns:
            List[List[float]]: 埋め込みベクトルのリスト
            
        Raises:
            Exception: 埋め込み処理に失敗した場合
        """
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        payload = {
            "input": texts
        }
        
        try:
            response = requests.post(
                self.embeddings_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Azure OpenAI APIのレスポンス形式:
            # {
            #   "data": [
            #     {"embedding": [...], "index": 0},
            #     {"embedding": [...], "index": 1}
            #   ]
            # }
            if "data" not in result:
                raise ValueError(f"予期しないレスポンスフォーマット: {result}")
            
            # インデックス順にソートして埋め込みを抽出
            embeddings_data = sorted(result["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in embeddings_data]
            
            return embeddings
            
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Azure OpenAI API呼び出しに失敗: {e}。"
                f"エンドポイント: {self.embeddings_url}、テキスト数: {len(texts)}"
            )
        except (KeyError, ValueError) as e:
            raise Exception(
                f"Azure OpenAI APIレスポンスの解析に失敗: {e}。"
                f"レスポンス: {response.text if 'response' in locals() else 'N/A'}"
            )
