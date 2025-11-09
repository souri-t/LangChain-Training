# RAG WebAPI サーバー

独立した FastAPI WebAPI サーバー。
Streamlit UI とは完全に分離して動作します。

## 概要

- **ファイル一覧取得**: `/api/files` (GET)
- **キーワード検索**: `/api/search` (POST)

## セットアップ

### 1. 依存関係をインストール

```bash
cd /workspace/RAG/rag_api
pip install -r requirements.txt
```

### 2. 設定ファイルをコピー

Streamlit アプリの `config.yaml` を共有使用します。
必要に応じて環境変数で接続先を指定できます。

## 起動方法

### 開発モード（ホットリロード有効）

```bash
cd /workspace/RAG/rag_api
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 本番モード

```bash
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

## アクセス

- **API ドキュメント (Swagger UI)**: http://localhost:8000/docs
- **API リファレンス (ReDoc)**: http://localhost:8000/redoc
- **ヘルスチェック**: http://localhost:8000/health

## API エンドポイント

### ファイル一覧取得

```bash
curl -X GET "http://localhost:8000/api/files"
```

### キーワード検索

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"Google","threshold":0.2,"n_results":5}'
```

## 詳細ドキュメント

- 詳細な仕様は同ディレクトリの `API_SPEC.md` を参照
- テストは `test_api.py` を実行

## 前提条件

- Ollama が起動していること（ローカル実行の場合）
- ChromaDB データが `/workspace/RAG/chroma_db` に存在すること
- Streamlit アプリとの共有リソースを使用
