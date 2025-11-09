# RAG WebAPI サーバー

検索機能とファイル一覧取得機能をWebAPIとして提供するFastAPIサーバーです。

## 概要

このWebAPIサーバーは、ChromaDB RAGアプリケーションの以下の機能をRESTful APIとして公開します：

- **ファイル一覧取得**: `/api/files` - 登録済みファイルの一覧を取得
- **キーワード検索**: `/api/search` - テキストから類似ドキュメントを検索

## 前提条件

### 必要なライブラリ

```bash
pip install fastapi uvicorn
```

または requirements.txt に以下が含まれていることを確認：
- `fastapi>=0.100.0`
- `uvicorn>=0.23.0`
- `pydantic>=2.0.0`

## 起動方法

### 開発モード（ホットリロード有効）

```bash
cd /workspace/RAG/rag_chroma_app
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 本番モード（ホットリロード無効）

```bash
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Python スクリプトから起動

```bash
python3 api_server.py
```

## API ドキュメント

サーバー起動後、以下のURLでAPI仕様を確認できます：

### Swagger UI（対話型）
```
http://localhost:8000/docs
```

### ReDoc（読み取り専用）
```
http://localhost:8000/redoc
```

## エンドポイント一覧

### 1. ヘルスチェック
```
GET /health
```
サーバーの状態確認用

**レスポンス例:**
```json
{
  "status": "healthy"
}
```

---

### 2. ファイル一覧取得
```
GET /api/files
```

**レスポンス例:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "filename": "google.txt",
        "directory": "/",
        "created_at": "2025-11-09T10:30:45",
        "doc_id": "doc_0"
      }
    ],
    "total_count": 8
  }
}
```

詳細は `API_SPEC.md` を参照

---

### 3. キーワード検索
```
POST /api/search
Content-Type: application/json

{
  "query": "Google",
  "threshold": 0.2,
  "n_results": 5
}
```

**パラメータ:**
- `query` (string, 必須): 検索キーワード
- `threshold` (float, オプション): 類似度閾値（0.0～1.0、デフォルト: 0.2）
- `n_results` (int, オプション): 返却する最大件数（1～100、デフォルト: 5）

**レスポンス例:**
```json
{
  "success": true,
  "data": {
    "query": "Google",
    "threshold": 0.2,
    "hit_count": 3,
    "results": [
      {
        "rank": 1,
        "filename": "google.txt",
        "score": 0.4557,
        "document": "## Google LLC（グーグル）会社情報まとめ...",
        "created_at": null
      }
    ]
  }
}
```

詳細は `API_SPEC.md` を参照

---

## テスト方法

### Python テストスクリプト

```bash
# テストスクリプトを実行（サーバーが起動している状態で）
python3 test_api.py
```

このスクリプトは以下をテストします：
- ヘルスチェック
- ファイル一覧取得
- 基本検索
- 高い閾値での検索
- エラーハンドリング（空のクエリ、無効な閾値など）
- 結果なしの検索

### cURL でのテスト

**ファイル一覧取得:**
```bash
curl -X GET "http://localhost:8000/api/files" \
  -H "Content-Type: application/json"
```

**検索:**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Google",
    "threshold": 0.2,
    "n_results": 5
  }'
```

### JavaScript / fetch でのテスト

```javascript
// ファイル一覧取得
fetch('http://localhost:8000/api/files')
  .then(res => res.json())
  .then(data => console.log(data));

// 検索
fetch('http://localhost:8000/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Google',
    threshold: 0.2,
    n_results: 5
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### Python requests でのテスト

```python
import requests

# ファイル一覧取得
response = requests.get("http://localhost:8000/api/files")
print(response.json())

# 検索
response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "Google",
        "threshold": 0.2,
        "n_results": 5
    }
)
print(response.json())
```

## 設定

APIサーバーは `config.yaml` の以下の設定を使用します：

```yaml
embedder:
  type: "generic"  # 埋め込みバックエンド

generic:
  api_key: ""
  embedding_url: "http://host.docker.internal:11434/api/embeddings"
  model: "embeddinggemma:latest"

chroma:
  persist_directory: "/workspace/RAG/chroma_db"
```

設定を変更する場合は、サーバーを再起動してください。

## エラーハンドリング

APIは以下のHTTPステータスコードを返します：

| コード | 説明 | 例 |
|-------|------|------|
| 200 | 成功 | 検索結果またはファイル一覧を返却 |
| 400 | リクエスト検証エラー | 無効なパラメータ（空のクエリ、閾値1.5など） |
| 404 | 結果が見つからない | 条件に合致するドキュメントがない |
| 500 | サーバーエラー | ベクトル化やChromaDB接続エラー |

**エラーレスポンス例:**
```json
{
  "success": false,
  "error": "検索結果が見つかりません",
  "details": "条件に合致するドキュメントがありません。"
}
```

## CORS設定

現在、全てのオリジン（`*`）からのリクエストを許可しています。

本番環境では、以下のように制限することを推奨します：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # 特定のドメインのみ許可
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

## パフォーマンス考慮事項

### ベクトル化処理
- 初回リクエスト時はモデルの読み込みに時間がかかる場合があります
- Ollama をローカルで実行している場合は、メモリとCPUリソースを確認してください

### 検索結果
- デフォルトは5件ですが、`n_results` で最大100件まで指定可能
- 大量の検索結果が必要な場合は、ページネーション機能の追加を検討してください

## ログ出力

Uvicornはデフォルトで全てのリクエスト・レスポンスをログ出力します：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started server process [12345]
INFO:     GET http://localhost:8000/health - 200 OK
INFO:     POST http://localhost:8000/api/search - 200 OK
```

ログレベルを変更する場合：
```bash
python3 -m uvicorn api_server:app --log-level debug
```

## 今後の拡張予定

- [ ] JWT認証の追加
- [ ] レート制限（rate limiting）
- [ ] 検索結果のキャッシング
- [ ] ファイル削除API
- [ ] ファイルアップロードAPI
- [ ] ページネーション
- [ ] 日本語のドキュメント検索フィルター
- [ ] メトリクス監視（Prometheus）

## トラブルシューティング

### Q: サーバーが起動しない
**A:** requirements.txtでfastapi, uvicornがインストールされていることを確認してください
```bash
pip install fastapi uvicorn pydantic
```

### Q: 404 "検索結果が見つかりません" エラーが出る
**A:** 登録ページからファイルをアップロードしているか確認してください

### Q: ファイル一覧取得が遅い
**A:** 登録済みドキュメント数が多い場合は時間がかかります。大量のドキュメント対応にはページネーション実装を推奨します

### Q: Ollama が見つからないエラーが出る
**A:** `config.yaml` の `generic.embedding_url` が正しいか確認してください
```yaml
generic:
  embedding_url: "http://host.docker.internal:11434/api/embeddings"
```

## ライセンス

このプロジェクトに準じます

## 関連ファイル

- `API_SPEC.md`: 詳細なAPI仕様書
- `api_server.py`: WebAPIサーバーメインコード
- `test_api.py`: テストスクリプト
- `config.yaml`: 設定ファイル
