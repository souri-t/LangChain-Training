# RagApp (C# .NET 8)

Python版RAG/rag_chroma_appのC#実装です。ASP.NET Core (.NET 8)を使用しています。

## 機能

- **ファイル登録**: テキストファイルまたはPDFをアップロードし、ベクトル化
- **検索**: 登録したドキュメントから類似度検索
- **ファイル一覧**: 登録済みファイルの確認と削除
- **UI**: Pythonのstreamlit版と同様の3ページ構成（ファイル登録・検索・ファイル一覧）

## 実行方法

```bash
cd /workspace/MSAgentFramework/RagApp
dotnet run --urls "http://0.0.0.0:5002"
```

ブラウザで `http://localhost:5002` を開く

## 設定

### Embedder

`Program.cs`でEmbedderの実装を選択します。

**デフォルト（テスト用）**:
```csharp
builder.Services.AddScoped<IEmbedder, MockEmbedder>();
```

**実際のAPIを使う場合**:
```csharp
builder.Services.AddScoped<IEmbedder, GenericEmbedder>();
```

`GenericEmbedder`を使う場合は`appsettings.json`で設定:
```json
{
  "Embedder": {
    "ApiKey": "your-api-key",
    "EmbeddingUrl": "http://localhost:11434/api/embeddings",
    "Model": "nomic-embed-text"
  }
}
```

対応API:
- Ollama: `http://localhost:11434/api/embeddings`
- Azure OpenAI
- OpenRouter

## API エンドポイント

- `GET /api/files/list` — ファイル一覧取得
- `POST /api/files/upload` — ファイルアップロード
- `POST /api/files/delete` — ファイル削除
- `POST /api/search` — 検索

## テスト例

```bash
# ファイルアップロード
curl -X POST -F "files=@/tmp/test.txt" http://localhost:5002/api/files/upload

# ファイル一覧
curl http://localhost:5002/api/files/list

# 検索
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"テスト","preview_chars":100,"score_threshold":0.5}' \
  http://localhost:5002/api/search
```

## 技術スタック

- ASP.NET Core 8.0
- Entity Framework Core + SQLite
- PdfPig (PDF処理)
- OpenAI互換API (埋め込み)
