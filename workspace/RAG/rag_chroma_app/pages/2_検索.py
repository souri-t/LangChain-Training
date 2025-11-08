
"""
検索ワードによるベクトル検索・スコア閾値フィルタを行うStreamlitページ。
OpenRouter埋め込み・ChromaDB検索・スコア表示に対応。
"""

import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import config
from openrouter_embedder import OpenRouterEmbedder
from chroma_manager import ChromaManager

st.title("検索ページ")



query = st.text_input("検索ワードを入力してください")
# 類似度閾値をUIで調整可能に
threshold = st.slider("スコア閾値（0.0〜1.0）", min_value=0.0, max_value=1.0, value=0.7, step=0.01)


# 検索処理
if st.button("検索"):
    """
    入力クエリをOpenRouterでベクトル化し、ChromaDBで類似検索を実行する。
    スコア閾値以上の結果のみを表示する。
    """
    if not query:
        st.warning("検索ワードを入力してください。")
    else:
        try:
            embedder = OpenRouterEmbedder(
                api_key=config['openrouter']['api_key'],
                embedding_url=config['openrouter']['embedding_url'],
                model=config['openrouter']['model']
            )
            embedding = embedder.embed([query])[0]
            chroma = ChromaManager(persist_directory=config['chroma']['persist_directory'])
            # query_embeddingsを使う場合はquery_texts=None
            result = chroma.query(query_texts=None, n_results=5, embeddings=[embedding])
            docs = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            scores = result.get("distances", [[]])[0]  # ChromaDBは"distances"で類似度（小さいほど近い）
            # スコアを1-距離で正規化（cosine類似度想定）
            sim_scores = [1 - s if s is not None else 0 for s in scores]
            st.subheader(f"検索結果（閾値: {threshold:.2f} 以上のみ表示）")
            found = False
            for i, (doc, score) in enumerate(zip(docs, sim_scores)):
                if score >= threshold:
                    found = True
                    meta = metadatas[i] if i < len(metadatas) else {}
                    st.markdown(f"**{i+1}. ファイル名:** {meta.get('filename', 'N/A')}")
                    st.markdown(f"**スコア:** {score:.3f}")
                    st.code(doc)
            if not found:
                st.info("該当するドキュメントが見つかりませんでした。")
        except Exception as e:
            st.error(f"検索処理でエラー: {e}")
