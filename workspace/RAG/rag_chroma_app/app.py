# Streamlitアプリのエントリポイント

# Streamlitアプリのエントリポイント

"""
Chroma RAGアプリのStreamlitエントリポイント。
設定ファイルの読込とトップページUIの表示を行う。
"""

import streamlit as st
import yaml

st.set_page_config(page_title="Chroma RAG App", layout="wide")

st.title("Chroma RAG アプリ")

st.write("左のサイドバーからページを選択してください。")

def load_config():
    """
    config.yamlから設定値を読み込む関数。
    Returns:
        dict: 設定値辞書
    """
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
