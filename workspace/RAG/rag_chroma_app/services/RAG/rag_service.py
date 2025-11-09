"""
RAGサービスクラス。
ファイル管理・検索・一覧表示の全機能を統合したサービスクラス。
ChromaDB操作もこのクラスに統合。
任意の Embedder を使用可能（プラグイン型設計）。
"""

from typing import List, Dict
from datetime import datetime
import sys
import os
import chromadb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.Vector.base_embedder import BaseEmbedder


class RAGService:
    """
    RAG（Retrieval-Augmented Generation）サービスの抽象基底クラス。
    ファイル登録・管理・検索機能を統合提供する。
    ChromaDB操作も内部に統合。
    任意の BaseEmbedder を使用可能。
    """

    def __init__(self, embedder: BaseEmbedder, chroma_persist_directory: str):
        """
        RAGサービスの初期化。
        Args:
            embedder (BaseEmbedder): 使用する埋め込みクライアント（OpenRouterEmbedder, OllamaEmbedder など）
            chroma_persist_directory (str): ChromaDBの永続ディレクトリ
        Raises:
            ValueError: chroma_persist_directoryが未指定の場合、または embedder が BaseEmbedder でない場合
        """
        if not chroma_persist_directory:
            raise ValueError("ChromaDBの永続化ディレクトリ（persist_directory）が未指定である。設定ファイルで明示的に指定すること。")
        
        if not isinstance(embedder, BaseEmbedder):
            raise ValueError(f"embedder は BaseEmbedder の実装である必要があります。受け取ったタイプ: {type(embedder)}")
        
        self.embedder = embedder
        # ChromaDB初期化
        self.client = chromadb.PersistentClient(path=chroma_persist_directory)
        self.collection = self.client.get_or_create_collection("rag_collection")

    def vectorize_and_register(self, texts: List[str], filenames: List[str]) -> None:
        """
        テキストリストをベクトル化し、ChromaDBに登録する。
        既存のファイル名は上書き登録される。
        Args:
            texts (List[str]): 登録するテキストリスト
            filenames (List[str]): 各テキストに対応するファイル名リスト
        Raises:
            Exception: ベクトル化・登録処理でエラーが発生した場合
        """
        # embedder を使ってベクトル化
        embeddings = self.embedder.embed(texts)
        # 既存ファイルを削除してから登録
        for fn in filenames:
            self._delete_by_filename(fn)
        # メタデータ作成（登録日時・ディレクトリ）
        now = datetime.now().isoformat(timespec='seconds')
        metadatas = [{"filename": fn, "created_at": now, "directory": "/"} for fn in filenames]
        # ChromaDB登録
        self._add_documents(texts, metadatas=metadatas, embeddings=embeddings)

    def _add_documents(self, texts: List[str], metadatas: List[dict] = None, embeddings: List[List[float]] = None) -> None:
        """
        ドキュメントをChromaDBコレクションに追加する。
        内部メソッド。必要に応じてメタデータや埋め込みベクトルも同時に登録可能。
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

    def _query(self, query_texts: List[str] = None, n_results: int = 5, embeddings: List[List[float]] = None) -> Dict:
        """
        クエリテキストまたは埋め込みベクトルで類似検索を実行する。
        内部メソッド。
        Args:
            query_texts (List[str], optional): 検索クエリのテキストリスト
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

    def _delete_by_filename(self, filename: str) -> None:
        """
        指定したファイル名に一致するドキュメントをコレクションから削除する。
        内部メソッド。
        Args:
            filename (str): 削除対象のファイル名
        """
        ids_to_delete = []
        all_docs = self.collection.get()
        for doc_id, meta in zip(all_docs.get('ids', []), all_docs.get('metadatas', [])):
            if meta.get('filename') == filename:
                ids_to_delete.append(doc_id)
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

    def _update_metadata(self, doc_id: str, new_metadata: dict) -> None:
        """
        指定したドキュメントのメタデータのみを更新する。
        内部メソッド。embedding次元不一致エラーを回避する。
        Args:
            doc_id (str): 更新対象のドキュメントID
            new_metadata (dict): 新しいメタデータ
        Raises:
            Exception: メタデータ更新処理でエラーが発生した場合
        """
        try:
            # collection.updateでメタデータのみ更新（ChromaDB公式APIの推奨方法）
            # ドキュメント本体・embeddingは変更せず、メタデータのみ変更
            self.collection.update(
                ids=[doc_id],
                metadatas=[new_metadata]
            )
        except Exception as e:
            raise Exception(f"メタデータ更新エラー: {e}")


    def search(self, query: str, n_results: int = 5, threshold: float = 0.7) -> List[Dict]:
        """
        クエリ検索を実行し、スコア閾値以上の結果を返す。
        Args:
            query (str): 検索クエリ
            n_results (int): 最大返却件数
            threshold (float): スコア閾値（0.0〜1.0）
        Returns:
            List[Dict]: 検索結果リスト（各要素は{"filename", "score", "document"}を含む辞書）
        """
        # クエリをベクトル化
        embedding = self.embedder.embed([query])[0]
        
        # ChromaDB検索
        result = self._query(query_texts=None, n_results=n_results, embeddings=[embedding])
        
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        scores = result.get("distances", [[]])[0]
        
        search_results = []
        for i, (doc, meta, score) in enumerate(zip(docs, metadatas, scores)):
            # L2距離を類似度に変換
            # L2距離では距離が小さいほど類似度が高い
            # 式: similarity = 1 / (1 + distance)
            # これにより、距離0 → 類似度1, 距離∞ → 類似度0 となる
            similarity = 1.0 / (1.0 + score)
            
            if similarity >= threshold:
                search_results.append({
                    "filename": meta.get("filename", "(不明)"),
                    "score": round(similarity, 4),
                    "document": doc
                })
        
        return search_results

    def get_file_list(self) -> List[Dict]:
        """
        登録済みファイル一覧を取得する。
        Returns:
            List[Dict]: ファイル情報リスト（各要素は{"filename", "directory", "created_at", "doc_id"}を含む辞書）
        """
        result = self.collection.get()
        metadatas = result.get("metadatas", [])
        ids = result.get("ids", [])
        
        file_list = []
        for i, meta in enumerate(metadatas):
            file_list.append({
                "filename": meta.get("filename", "(不明)"),
                "directory": meta.get("directory", "/"),
                "created_at": meta.get("created_at", "-"),
                "doc_id": ids[i] if i < len(ids) else None
            })
        
        return file_list

    def update_directories(self, updates: List[Dict]) -> None:
        """
        複数ファイルのディレクトリを一括更新する。
        Args:
            updates (List[Dict]): 更新情報リスト（各要素は{"doc_id", "new_directory"}を含む辞書）
        Raises:
            Exception: 更新処理でエラーが発生した場合
        """
        result = self.collection.get()
        metadatas = result.get("metadatas", [])
        ids = result.get("ids", [])
        
        for update in updates:
            doc_id = update.get("doc_id")
            new_directory = update.get("new_directory")
            
            if doc_id and doc_id in ids:
                idx = ids.index(doc_id)
                new_meta = dict(metadatas[idx])
                new_meta["directory"] = new_directory
                self._update_metadata(doc_id, new_meta)
