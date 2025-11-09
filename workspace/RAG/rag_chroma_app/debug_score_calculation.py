"""
ChromaDB の距離計算とスコア変換をデバッグするスクリプト。
異なるモデルでのスコア分布を確認する。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.Vector.generic_embedder import GenericEmbedder
from services.RAG.rag_service import RAGService
import yaml

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# Ollama の Embedder を作成
embedder = GenericEmbedder(
    api_key=config['generic']['api_key'],
    embedding_url=config['generic']['embedding_url'],
    model=config['generic']['model']
)

# RAGService を初期化
rag_service = RAGService(
    embedder=embedder,
    chroma_persist_directory=config['chroma']['persist_directory']
)

# テストクエリと登録済みドキュメントを比較
test_queries = [
    "test document",
    "embeddings",
    "vector search",
]

print("=" * 80)
print("デバッグ: スコア計算")
print("=" * 80)
print(f"使用モデル: {config['generic']['model']}")
print(f"エンドポイント: {config['generic']['embedding_url']}")
print()

# 登録済みドキュメントを取得
all_docs = rag_service.collection.get()
print(f"登録済みドキュメント数: {len(all_docs.get('documents', []))}")
print()

if len(all_docs.get('documents', [])) > 0:
    # 最初のドキュメントを取得
    first_doc = all_docs.get('documents', [])[0]
    print(f"最初のドキュメント（先頭100文字）: {first_doc[:100]}")
    print()
    
    # 各テストクエリで検索
    for query in test_queries:
        print(f"\n--- クエリ: '{query}' ---")
        
        # クエリをベクトル化
        query_embedding = embedder.embed([query])[0]
        print(f"クエリの埋め込みベクトル次元数: {len(query_embedding)}")
        
        # ChromaDB で検索
        result = rag_service._query(query_texts=None, n_results=5, embeddings=[query_embedding])
        
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        scores = result.get("distances", [[]])[0]
        
        print(f"\n検索結果数: {len(docs)}")
        
        for i, (doc, meta, raw_score) in enumerate(zip(docs, metadatas, scores)):
            # スコアを類似度に変換
            similarity = 1 - raw_score
            
            print(f"\n  結果 {i+1}:")
            print(f"    ファイル名: {meta.get('filename', '(不明)')}")
            print(f"    距離（生値）: {raw_score:.6f}")
            print(f"    類似度（1-距離）: {similarity:.6f}")
            print(f"    ドキュメント（先頭50文字）: {doc[:50]}")

else:
    print("登録済みドキュメントがありません。")
    print("先に登録ページでファイルをアップロードしてください。")
