
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
    st.subheader("登録済みファイル一覧（表形式）")
    if metadatas:
        # 一括編集用のセッション状態を初期化
        if 'dir_edits' not in st.session_state or len(st.session_state['dir_edits']) != len(metadatas):
            st.session_state['dir_edits'] = [meta.get("directory", "/") for meta in metadatas]

        st.subheader("ディレクトリ一括編集")
        if st.button("すべて保存", key="save_all"):
            try:
                all_ids = result.get("ids", [])
                for i, meta in enumerate(metadatas):
                    doc_id = all_ids[i] if i < len(all_ids) else None
                    if doc_id:
                        new_meta = dict(meta)
                        new_meta["directory"] = st.session_state['dir_edits'][i]
                        # ChromaManagerの更新メソッドを使用
                        chroma.update_metadata(doc_id, new_meta)
                st.success("すべてのディレクトリを更新しました。ページを再読み込みしてください。")
            except Exception as e:
                st.error(f"保存処理でエラーが発生しました: {e}")

        # テーブルの各行にテキストボックスを配置
        st.caption("※ディレクトリ列は直接編集できます。編集後『すべて保存』ボタンで一括反映できます。")
        # st.tableで静的表示
        import pandas as pd
        rows = []
        for i, meta in enumerate(metadatas):
            fn = meta.get("filename", "(不明)")
            directory = st.session_state['dir_edits'][i]
            created = meta.get("created_at", "-")
            rows.append({
                "ファイル名": fn,
                "ディレクトリ": directory,
                "登録日時": created
            })
        df = pd.DataFrame(rows)
        st.table(df)

        st.caption("※下の各行でディレクトリを編集後、『すべて保存』ボタンで一括反映できます。")
        st.markdown("---")
        st.write("### ディレクトリ編集欄")
        for i, meta in enumerate(metadatas):
            fn = meta.get("filename", "(不明)")
            col1, col2, col3 = st.columns([1, 5, 6])
            col1.write(i+1)
            col2.write(fn)
            new_dir = col3.text_input("", value=st.session_state['dir_edits'][i], key=f"edit_dir_{i}")
            st.session_state['dir_edits'][i] = new_dir
    else:
        st.info("登録ファイルはありません。")
except Exception as e:
    st.error(f"ファイル一覧取得でエラー: {e}")
