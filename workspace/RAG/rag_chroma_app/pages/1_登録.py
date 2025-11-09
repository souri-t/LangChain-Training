"""
ファイルアップロード・ベクトル化・ChromaDB登録を行うStreamlitページ。
PDF・テキストファイルの読み込み、埋め込み生成、同名ファイルの上書き登録に対応。
設定ファイルで Generic（OpenRouter/Ollama）, Azure OpenAI, Sentence-Transformers を選択可能。
"""
import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import config
from services.RAG.rag_service import RAGService
from services.Vector.generic_embedder import GenericEmbedder
from services.Vector.azure_openai_embedder import AzureOpenAIEmbedder
from services.Vector.sentence_transformer_service import SentenceTransformerEmbedder
from utils import extract_text_from_pdf


def create_embedder():
    """
    config.yaml の embedder.type に基づいて、適切な Embedder インスタンスを作成する。
    Returns:
        BaseEmbedder: GenericEmbedder, AzureOpenAIEmbedder, または SentenceTransformerEmbedder のインスタンス
    Raises:
        ValueError: 不正な embedder.type が指定された場合
    """
    embedder_type = config.get('embedder', {}).get('type', 'generic')
    
    if embedder_type == 'generic':
        return GenericEmbedder(
            api_key=config['generic']['api_key'],
            embedding_url=config['generic']['embedding_url'],
            model=config['generic']['model']
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
        raise ValueError(f"不正な embedder.type: {embedder_type}。'generic', 'azure-openai', または 'sentence-transformer' を指定してください。")


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
    アップロード済みテキストを config で指定された Embedder を使用してベクトル化し、ChromaDBに登録する。
    既存ファイル名は上書き登録とする。
    """
    if not st.session_state['texts']:
        st.warning("先にファイルをアップロードしてください。")
    else:
        try:
            # config で指定された Embedder を作成
            embedder = create_embedder()
            
            # RAGService を初期化（embedder をインジェクション）
            rag_service = RAGService(
                embedder=embedder,
                chroma_persist_directory=config['chroma']['persist_directory']
            )
            
            # ベクトル化・登録
            rag_service.vectorize_and_register(
                st.session_state['texts'],
                st.session_state['uploaded_files']
            )
            st.session_state['vectorized'] = True
            embedder_type = config.get('embedder', {}).get('type', 'openrouter')
            st.success(f"ベクトル化（{embedder_type}）＆ChromaDB登録が完了しました。")
        except Exception as e:
            st.error(f"ベクトル化処理でエラー: {e}")

