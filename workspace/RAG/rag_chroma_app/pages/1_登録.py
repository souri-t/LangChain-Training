"""
ファイルアップロード・ベクトル化・ChromaDB登録を行うStreamlitページ。
PDF・テキストファイルの読み込み、埋め込み生成、同名ファイルの上書き登録に対応。
"""
import streamlit as st
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import config
from openrouter_embedder import OpenRouterEmbedder
from chroma_manager import ChromaManager
from utils import extract_text_from_pdf

st.title("ファイル登録ページ")



# セッション状態の初期化
if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []
if 'texts' not in st.session_state:
    st.session_state['texts'] = []
if 'vectorized' not in st.session_state:
    st.session_state['vectorized'] = False


uploaded_files = st.file_uploader("テキストファイルまたはPDFをアップロード", type=["txt", "pdf"], accept_multiple_files=True)


# ファイルアップロード処理
if uploaded_files:
    """
    アップロードされたファイルを読み込み、テキスト抽出・セッション保存を行う。
    同名ファイルは上書き対象とする。
    """
    st.session_state['uploaded_files'] = []
    st.session_state['texts'] = []
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.txt'):
            text = uploaded_file.read().decode('utf-8')
        elif uploaded_file.name.endswith('.pdf'):
            text = extract_text_from_pdf(uploaded_file)
        else:
            text = ''
        st.session_state['uploaded_files'].append(uploaded_file.name)
        st.session_state['texts'].append(text)
    st.session_state['vectorized'] = False
    st.success(f"{len(uploaded_files)}件のファイルを読み込みました。")



# ベクトル化・ChromaDB登録処理
if st.button("ベクトル化"):
    """
    アップロード済みテキストをOpenRouterでベクトル化し、ChromaDBに登録する。
    既存ファイル名は上書き登録とする。
    """
    if not st.session_state['texts']:
        st.warning("先にファイルをアップロードしてください。")
    else:
        try:
            embedder = OpenRouterEmbedder(
                api_key=config['openrouter']['api_key'],
                embedding_url=config['openrouter']['embedding_url'],
                model=config['openrouter']['model']
            )
            embeddings = embedder.embed(st.session_state['texts'])
            chroma = ChromaManager(persist_directory=config['chroma']['persist_directory'])
            # 既存ファイル名があれば削除してから追加
            for fn in st.session_state['uploaded_files']:
                chroma.delete_by_filename(fn)
            now = datetime.now().isoformat(timespec='seconds')
            # ディレクトリパス（初期値は空文字列、将来変更可能）もメタデータに追加
            metadatas = [{"filename": fn, "created_at": now, "directory": "/"} for fn in st.session_state['uploaded_files']]
            chroma.add_documents(st.session_state['texts'], metadatas=metadatas, embeddings=embeddings)
            st.session_state['vectorized'] = True
            st.success("ベクトル化＆ChromaDB登録が完了しました。")
        except Exception as e:
            st.error(f"ベクトル化処理でエラー: {e}")
