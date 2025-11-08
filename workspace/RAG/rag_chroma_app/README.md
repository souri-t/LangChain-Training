# Chroma RAG App

## 概要
ChromaとOpenRouter埋め込みモデルを使ったRAG（Retrieval Augmented Generation）デモアプリです。Streamlitで動作します。

## 機能
- ファイル登録（.txt, .pdf）
- ベクトル化（OpenRouter API利用）
- ChromaDBへの登録
- 検索（ベクトル検索）

## セットアップ
1. Python 3.18 を用意してください。
2. 必要なパッケージをインストールします。
   ```sh
   pip install -r requirements.txt
   ```
3. OpenRouterのAPIキー・モデル・エンドポイントを環境変数に設定してください。
   ```sh
   export OPENROUTER_API_KEY=sk-xxxxxxx
   export OPENROUTER_MODEL=text-embedding-ada-002  # 利用するモデル名
   export OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/embeddings  # 必要に応じて変更
   ```
4. Streamlitアプリを起動します。
   ```sh
   streamlit run app.py
   ```

## ディレクトリ構成
- app.py : Streamlitエントリポイント
- pages/ : 登録・検索ページ
- utils.py : PDFテキスト抽出ユーティリティ
- openrouter_embedder.py : OpenRouter埋め込みAPIラッパー
- chroma_manager.py : ChromaDB管理

## 注意
- OpenRouterのAPIキー・モデル・エンドポイントが必要です。
- ChromaDBはローカルに永続化されます。
