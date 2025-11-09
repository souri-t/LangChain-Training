
"""
検索ワードによるベクトル検索・スコア閾値フィルタを行うStreamlitページ。
設定ファイルで指定された Embedder（Generic, Azure OpenAI, Sentence-Transformers）で埋め込み・検索に対応。
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


st.title("検索ページ")

query = st.text_input("検索ワードを入力してください")
# 類似度閾値をUIで調整可能に
threshold = st.slider("スコア閾値（0.0〜1.0）", min_value=0.0, max_value=1.0, value=0.2, step=0.01)

# プレビュー文字数の設定
preview_chars = st.slider("プレビュー表示文字数", min_value=50, max_value=2000, value=500, step=50)

# 検索処理
if st.button("検索"):
    """
    入力クエリを config で指定された Embedder を使用してベクトル化し、ChromaDBで類似検索を実行する。
    スコア閾値以上の結果のみを表示する。
    """
    if not query:
        st.warning("検索ワードを入力してください。")
    else:
        try:
            # config で指定された Embedder を作成
            embedder = create_embedder()
            
            # RAGService を初期化（embedder をインジェクション）
            rag_service = RAGService(
                embedder=embedder,
                chroma_persist_directory=config['chroma']['persist_directory']
            )
            
            results = rag_service.search(query, n_results=5, threshold=threshold)
            
            st.subheader(f"検索結果（閾値: {threshold:.2f} 以上のみ表示）")
            if results:
                # ヒット件数を表示
                st.success(f"✓ {len(results)} 件ヒットしました")
                st.divider()
                
                for i, result in enumerate(results):
                    st.markdown(f"**{i+1}. ファイル名:** {result['filename']}")
                    st.markdown(f"**スコア:** {result['score']}")
                    st.text(f"内容: {result['document'][:preview_chars]}...")
                    st.divider()
            else:
                st.info("条件に合致する結果がありません。")
        except Exception as e:
            st.error(f"検索処理でエラー: {e}")
