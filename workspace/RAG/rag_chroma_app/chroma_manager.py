
"""
ChromaDBの管理を行うクラス群。
ドキュメントの追加・検索・削除など、RAGアプリのベクトルストア操作を集約する。
"""

import chromadb
from typing import List


class ChromaManager:
    """
    ChromaDBのコレクション管理クラス。
    ドキュメントの追加・検索・削除などの操作を提供する。
    """

    def __init__(self, persist_directory: str):
        """
        ChromaDBの永続化ディレクトリを指定して初期化する。
        PersistentClientを利用し、指定パスにベクトルストアを永続化する。
        Args:
            persist_directory (str): ChromaDBの永続化ディレクトリパス
        Raises:
            ValueError: persist_directoryが未指定の場合
        """
        if not persist_directory:
            raise ValueError("ChromaDBの永続化ディレクトリ（persist_directory）が未指定である。設定ファイルで明示的に指定すること。")
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("rag_collection")

    def add_documents(self, texts: List[str], metadatas: List[dict] = None, embeddings: List[List[float]] = None):
        """
        ドキュメントをChromaDBコレクションに追加する。
        必要に応じてメタデータや埋め込みベクトルも同時に登録可能。
        Args:
            texts (List[str]): 登録するテキストリスト
            metadatas (List[dict], optional): 各テキストに対応するメタデータ辞書リスト
            embeddings (List[List[float]], optional): 各テキストの埋め込みベクトル
        """
        ids = [f"doc_{i}" for i in range(len(texts))]
        self.collection.add(
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids,
            embeddings=embeddings
        )

    def query(self, query_texts: List[str], n_results: int = 5, embeddings: List[List[float]] = None):
        """
        クエリテキストまたは埋め込みベクトルで類似検索を実行する。
        Args:
            query_texts (List[str]): 検索クエリのテキストリスト
            n_results (int): 返却する最大件数
            embeddings (List[List[float]], optional): クエリの埋め込みベクトル
        Returns:
            dict: 検索結果（ドキュメント・メタデータ・スコア等）
        """
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            query_embeddings=embeddings
        )

    def delete_by_filename(self, filename: str):
        """
        指定したファイル名に一致するドキュメントをコレクションから削除する。
        Args:
            filename (str): 削除対象のファイル名
        """
        ids_to_delete = []
        all = self.collection.get()
        for doc_id, meta in zip(all.get('ids', []), all.get('metadatas', [])):
            if meta.get('filename') == filename:
                ids_to_delete.append(doc_id)
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
