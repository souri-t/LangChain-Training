"""
OpenRouter埋め込みAPIクライアント
"""

from typing import List
import requests
from .base_embedder import BaseEmbedder


class OpenRouterEmbedder(BaseEmbedder):
    """
    OpenRouter埋め込みAPIクライアントクラス。
    指定モデル・エンドポイントでテキストから埋め込みベクトルを取得する。
    """

    def __init__(self, api_key: str, embedding_url: str, model: str):
        """
        OpenRouter埋め込みAPIクライアントの初期化。
        Args:
            api_key (str): OpenRouter APIキー
            embedding_url (str): 埋め込みAPIエンドポイントURL
            model (str): 埋め込みモデル名
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
            raise ValueError("OpenRouter埋め込みモデルが未指定である。コンストラクタ引数で指定すること。")
        if not self.embedding_url:
            raise ValueError("OpenRouter埋め込みエンドポイントURLが未指定である。コンストラクタ引数で指定すること。")

        data = {
            "input": texts,
            "model": self.model
        }
        response = requests.post(self.embedding_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return [item["embedding"] for item in result["data"]]
