
"""
ChromaDBに登録済みのファイル一覧を表示するStreamlitページ。
全ドキュメントのメタデータからファイル名を抽出しリスト表示する。
設定ファイルで指定された Embedder（OpenRouter, Azure OpenAI, Sentence-Transformers）に対応。
"""

import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import config
from services.RAG.rag_service import RAGService
from services.Vector.openrouter_file_service import OpenRouterEmbedder
from services.Vector.azure_openai_embedder import AzureOpenAIEmbedder
from services.Vector.sentence_transformer_service import SentenceTransformerEmbedder


def create_embedder():
    """
    config.yaml の embedder.type に基づいて、適切な Embedder インスタンスを作成する。
    Returns:
        BaseEmbedder: OpenRouterEmbedder, AzureOpenAIEmbedder, または SentenceTransformerEmbedder のインスタンス
    Raises:
        ValueError: 不正な embedder.type が指定された場合
    """
    embedder_type = config.get('embedder', {}).get('type', 'openrouter')
    
    if embedder_type == 'openrouter':
        return OpenRouterEmbedder(
            api_key=config['openrouter']['api_key'],
            embedding_url=config['openrouter']['embedding_url'],
            model=config['openrouter']['model']
        )
    elif embedder_type == 'azure-openai':
        return AzureOpenAIEmbedder(
            api_key=config['azure_openai']['api_key'],
            endpoint=config['azure_openai']['endpoint'],
            deployment_name=config['azure_openai']['deployment_name'],
            api_version=config['azure_openai'].get('api_version', '2024-02-01')
        )
    elif embedder_type == 'sentence-transformer':
        return SentenceTransformerEmbedder(
            model_name=config['sentence_transformer']['model_name']
        )
    else:
        raise ValueError(f"不正な embedder.type: {embedder_type}。'openrouter', 'azure-openai', または 'sentence-transformer' を指定してください。")


st.title("登録ファイル一覧")

# ファイル一覧取得・表示処理
try:
    """
    ChromaDBコレクションから全ドキュメントのファイル名を抽出し、リスト表示する。
    """
    # config で指定された Embedder を作成
    embedder = create_embedder()
    
    # RAGService を初期化（embedder をインジェクション）
    rag_service = RAGService(
        embedder=embedder,
        chroma_persist_directory=config['chroma']['persist_directory']
    )
    file_list = rag_service.get_file_list()
    
    st.subheader("登録済みファイル一覧（表形式）")
    if file_list:
        # 一括編集用のセッション状態を初期化
        if 'dir_edits' not in st.session_state or len(st.session_state['dir_edits']) != len(file_list):
            st.session_state['dir_edits'] = [f['directory'] for f in file_list]

        # テーブルの各行にテキストボックスを配置
        st.caption("※ディレクトリ列を参考にしてください。")
        # st.tableで静的表示
        import pandas as pd
        rows = []
        for i, file_info in enumerate(file_list):
            rows.append({
                "ファイル名": file_info['filename'],
                "ディレクトリ": st.session_state['dir_edits'][i],
                "登録日時": file_info['created_at']
            })
        df = pd.DataFrame(rows)
        st.table(df)

        st.caption("※下の各行でディレクトリを編集後、『すべて保存』ボタンで一括反映できます。")
        st.markdown("---")
        st.write("### ディレクトリ編集欄")
        for i, file_info in enumerate(file_list):
            col1, col2, col3 = st.columns([1, 5, 6])
            col1.write(i+1)
            col2.write(file_info['filename'])
            new_dir = col3.text_input("ディレクトリ", value=st.session_state['dir_edits'][i], key=f"edit_dir_{i}")
            st.session_state['dir_edits'][i] = new_dir
        
        # 「すべて保存」ボタンをディレクトリ編集欄の下に配置
        st.markdown("---")
        if st.button("すべて保存", key="save_all"):
            try:
                updates = []
                for i, file_info in enumerate(file_list):
                    updates.append({
                        "doc_id": file_info['doc_id'],
                        "new_directory": st.session_state['dir_edits'][i]
                    })
                rag_service.update_directories(updates)
                st.success("すべてのディレクトリを更新しました。ページを再読み込みしてください。")
            except Exception as e:
                st.error(f"保存処理でエラーが発生しました: {e}")
    else:
        st.info("登録ファイルはありません。")
except Exception as e:
    st.error(f"ファイル一覧取得でエラー: {e}")

