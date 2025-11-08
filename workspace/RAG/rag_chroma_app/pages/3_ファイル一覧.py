
"""
ChromaDBに登録済みのファイル一覧を表示するStreamlitページ。
全ドキュメントのメタデータからファイル名を抽出しリスト表示する。
"""

import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from chroma_manager import ChromaManager

st.title("登録ファイル一覧")


# ファイル一覧取得・表示処理
try:
    """
    ChromaDBコレクションから全ドキュメントのファイル名を抽出し、リスト表示する。
    """
    from app import config
    chroma = ChromaManager(persist_directory=config['chroma']['persist_directory'])
    # ChromaDBの全ドキュメントのメタデータを取得
    result = chroma.collection.get()
    metadatas = result.get("metadatas", [])
    filenames = [meta.get("filename", "(不明)") for meta in metadatas]
    st.subheader("登録済みファイル名")
    if filenames:
        for i, fn in enumerate(filenames):
            st.markdown(f"{i+1}. {fn}")
    else:
        st.info("登録ファイルはありません。")
except Exception as e:
    st.error(f"ファイル一覧取得でエラー: {e}")
