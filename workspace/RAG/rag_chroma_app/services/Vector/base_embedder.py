"""
埋め込みクライアントの抽象基底クラス。
すべての Embedder はこのインターフェースを実装する。
"""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """
    埋め込みクライアントの抽象基底クラス。
    OpenRouter、Ollama など、異なるバックエンドの Embedder はこれを継承する。
    """

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        テキストリストをベクトル化する。
        
        Args:
            texts (List[str]): ベクトル化するテキストリスト
            
        Returns:
            List[List[float]]: 各テキストに対応する埋め込みベクトルリスト
            
        Raises:
            Exception: 埋め込み処理に失敗した場合
        """
        pass
