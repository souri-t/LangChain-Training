# RAG WebAPI 仕様書

## 概要
ChromaDB RAGアプリの検索機能とファイル一覧取得機能をWebAPIとして提供します。
FastAPIを使用した高速・型安全なRESTful APIです。

## 技術スタック
- **フレームワーク**: FastAPI (async/await対応)
- **サーバー**: Uvicorn
- **データフォーマット**: JSON
- **ポート**: 8000 (デフォルト)

---

## エンドポイント

### 1. ファイル一覧取得

#### リクエスト
```
GET /api/files
```

#### レスポンス (200 OK)
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "filename": "Japan_Cabinet.txt",
        "directory": "/",
        "created_at": "2025-11-09T10:30:45",
        "doc_id": "doc_0"
      },
      {
        "filename": "UK_Cabinet.txt",
        "directory": "/",
        "created_at": "2025-11-09T10:31:12",
        "doc_id": "doc_1"
      }
    ],
    "total_count": 8
  }
}
```

#### レスポンス (500 Internal Server Error)
```json
{
  "success": false,
  "error": "ファイル一覧取得処理でエラー",
  "details": "エラーメッセージ"
}
```

---

### 2. キーワード検索

#### リクエスト
```
POST /api/search
Content-Type: application/json

{
  "query": "Google",
  "threshold": 0.2,
  "n_results": 5
}
```

#### リクエストパラメータ
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|-----|----------|------|
| `query` | string | ✓ | - | 検索クエリ（空でない） |
| `threshold` | float | ✗ | 0.2 | 類似度閾値（0.0～1.0） |
| `n_results` | int | ✗ | 5 | 返却する最大件数（1～100） |

#### レスポンス (200 OK)
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
        "document": "## Google LLC（グーグル）会社情報まとめ\n\n**会社名**：Google LLC（親会社Alphabet Inc.傘下）...",
        "created_at": "2025-11-09T10:30:45"
      },
      {
        "rank": 2,
        "filename": "alibana.txt",
        "score": 0.3735,
        "document": "## Alibaba Group Holding Limited（アリババグループ）会社情報まとめ...",
        "created_at": "2025-11-09T10:31:05"
      },
      {
        "rank": 3,
        "filename": "apple.txt",
        "score": 0.363,
        "document": "## Apple Inc.（アップル）会社情報まとめ...",
        "created_at": "2025-11-09T10:30:58"
      }
    ]
  }
}
```

#### レスポンス (400 Bad Request)
```json
{
  "success": false,
  "error": "リクエスト検証エラー",
  "details": {
    "query": "検索ワードを入力してください。",
    "threshold": "閾値は0.0～1.0の範囲内である必要があります。",
    "n_results": "返却件数は1～100である必要があります。"
  }
}
```

#### レスポンス (404 Not Found)
```json
{
  "success": false,
  "error": "検索結果が見つかりません",
  "details": "条件に合致するドキュメントがありません。"
}
```

#### レスポンス (500 Internal Server Error)
```json
{
  "success": false,
  "error": "検索処理でエラー",
  "details": "エラーメッセージ"
}
```

---

## レスポンス統一フォーマット

### 成功レスポンス
```json
{
  "success": true,
  "data": {
    // エンドポイント固有のデータ
  }
}
```

### エラーレスポンス
```json
{
  "success": false,
  "error": "エラータイトル",
  "details": "詳細情報 または オブジェクト"
}
```

---

## HTTP ステータスコード

| コード | 説明 |
|-------|------|
| 200 | 成功 |
| 400 | リクエスト検証エラー（無効なパラメータ） |
| 404 | リソースが見つからない |
| 500 | サーバーエラー |

---

## CORS設定
- **許可オリジン**: `*` (全て許可、本番環境では制限推奨)
- **許可メソッド**: GET, POST, OPTIONS
- **許可ヘッダー**: Content-Type, Authorization

---

## 設定
以下は `config.yaml` で指定された埋め込みモデルを自動的に使用：
- `embedder.type`: 埋め込みバックエンド（generic, azure-openai, sentence-transformer）
- `generic.embedding_url`: エンドポイントURL
- `generic.model`: モデル名
- `chroma.persist_directory`: ChromaDB永続ディレクトリ

---

## 実行方法

### サーバー起動
```bash
cd /workspace/RAG/rag_chroma_app
python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### API確認（Swagger UI）
ブラウザで以下にアクセス：
```
http://localhost:8000/docs
```

### API確認（ReDoc）
```
http://localhost:8000/redoc
```

---

## 使用例

### cURL でのファイル一覧取得
```bash
curl -X GET "http://localhost:8000/api/files" \
  -H "Content-Type: application/json"
```

### cURL での検索
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Google",
    "threshold": 0.2,
    "n_results": 5
  }'
```

### Python でのリクエスト例
```python
import requests

# ファイル一覧取得
response = requests.get("http://localhost:8000/api/files")
files = response.json()

# 検索
search_result = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "Google",
        "threshold": 0.2,
        "n_results": 5
    }
)
results = search_result.json()
```

### JavaScript での リクエスト例
```javascript
// ファイル一覧取得
fetch('http://localhost:8000/api/files')
  .then(response => response.json())
  .then(data => console.log(data));

// 検索
fetch('http://localhost:8000/api/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'Google',
    threshold: 0.2,
    n_results: 5
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## エラーハンドリング

### 検索クエリが空の場合
```json
{
  "success": false,
  "error": "リクエスト検証エラー",
  "details": {
    "query": "検索ワードを入力してください。"
  }
}
```

### 閾値が範囲外の場合
```json
{
  "success": false,
  "error": "リクエスト検証エラー",
  "details": {
    "threshold": "閾値は0.0～1.0の範囲内である必要があります。"
  }
}
```

### 返却件数が不正な場合
```json
{
  "success": false,
  "error": "リクエスト検証エラー",
  "details": {
    "n_results": "返却件数は1～100である必要があります。"
  }
}
```

---

## 今後の拡張可能性

- **認証**: JWT トークンベース認証の追加
- **キャッシング**: 頻繁なクエリ結果のキャッシュ
- **ロギング**: 全APIリクエストのログ記録
- **レート制限**: クライアント別のレート制限
- **ページング**: 大規模な検索結果のページネーション
- **フィルター**: ファイル名・ディレクトリ・日付による絞り込み
- **ファイル削除API**: DELETE /api/files/{filename}
- **ファイル登録API**: POST /api/upload (ファイルアップロード)

---

## 仕様版: v1.0.0
**最終更新**: 2025-11-09
