"""
Sentence-Transformers埋め込みクライアント
"""

from typing import List
from sentence_transformers import SentenceTransformer
from .base_embedder import BaseEmbedder


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Sentence-Transformers を使ってテキストをベクトル化するクラス。
    
    ローカルで動作し、事前学習済みモデルを自動ダウンロードして使用します。
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        SentenceTransformerEmbedderの初期化。
        
        Args:
            model_name (str): 使用するモデル名（デフォルト: all-MiniLM-L6-v2）
                              推奨モデル:
                              - all-MiniLM-L6-v2: 軽量・高速（384次元）
                              - paraphrase-multilingual-MiniLM-L12-v2: 多言語対応（384次元）
                              - all-mpnet-base-v2: 高精度（768次元）
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        テキストリストをSentence-Transformersでベクトル化する。
        
        Args:
            texts (List[str]): ベクトル化するテキストのリスト
            
        Returns:
            List[List[float]]: 埋め込みベクトルのリスト
            
        Raises:
            Exception: 埋め込み処理に失敗した場合
        """
        try:
            # Sentence-Transformersでテキストを埋め込み
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # numpy配列をリストに変換
            return embeddings.tolist()
                
        except Exception as e:
            raise Exception(
                f"Sentence-Transformers埋め込み処理に失敗: {e}。"
                f"モデル: {self.model_name}、テキスト数: {len(texts)}"
            )
