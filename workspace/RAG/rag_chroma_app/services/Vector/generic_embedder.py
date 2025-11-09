"""
OpenAI互換 API用の汎用埋め込みクライアント
OpenRouter、Ollama、Azure OpenAI など、OpenAI API 互換エンドポイントに対応
"""

from typing import List
import requests
from .base_embedder import BaseEmbedder


class GenericEmbedder(BaseEmbedder):
    """
    OpenAI API 互換エンドポイント用汎用埋め込みクライアントクラス。
    
    対応サービス:
    - OpenRouter（https://openrouter.ai/）
    - Ollama（http://localhost:11434）
    - その他 OpenAI API 互換エンドポイント
    
    指定モデル・エンドポイントでテキストから埋め込みベクトルを取得する。
    """

    def __init__(self, api_key: str, embedding_url: str, model: str):
        """
        汎用埋め込みクライアントの初期化。
        
        Args:
            api_key (str): APIキー（Ollama などのローカルサーバーでは空文字列でOK）
            embedding_url (str): 埋め込みAPIエンドポイントURL
                例:
                - OpenRouter: https://openrouter.ai/api/v1/embeddings
                - Ollama: http://localhost:11434/api/embeddings
            model (str): 埋め込みモデル名
                例:
                - OpenRouter: text-embedding-nomic-embed-text-v1.5@q8_0
                - Ollama: nomic-embed-text, mxbai-embed-large など
        """
        self.api_key = api_key
        self.embedding_url = embedding_url
        self.model = model

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        テキストリストから埋め込みベクトルを取得する。
        
        Args:
            texts (List[str]): 埋め込み対象のテキストリスト
            
        Returns:
            List[List[float]]: 各テキストに対応する埋め込みベクトルリスト
            
        Raises:
            ValueError: モデルまたはエンドポイント未指定時
            requests.HTTPError: APIリクエスト失敗時
        """
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if not self.model:
            raise ValueError("埋め込みモデルが未指定である。コンストラクタ引数で指定すること。")
        if not self.embedding_url:
            raise ValueError("埋め込みエンドポイントURLが未指定である。コンストラクタ引数で指定すること。")

        embeddings = []
        
        # Ollama の場合（/api/embeddings エンドポイント）
        if "/api/embeddings" in self.embedding_url:
            # Ollama は1テキストずつ処理する必要がある
            for text in texts:
                data = {
                    "model": self.model,
                    "prompt": text
                }
                response = requests.post(self.embedding_url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["embedding"])
        else:
            # OpenAI API 互換形式（OpenRouter など）
            data = {
                "input": texts,
                "model": self.model
            }
            response = requests.post(self.embedding_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
        
        return embeddings


# 互換性のためのエイリアス
OpenRouterEmbedder = GenericEmbedder
