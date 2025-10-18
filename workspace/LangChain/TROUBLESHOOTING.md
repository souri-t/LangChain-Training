# LM Studio使用時のトラブルシューティング

## 発生したエラー

```
Error code: 400 - {'error': 'Error rendering prompt with jinja template: "Conversation roles must alternate user/assistant/user/assistant/..."
```

## 問題の原因

LM Studioのローカルモデル（特にGemmaなど）は、会話の形式に非常に厳格な要件があります：

1. **メッセージは user → assistant → user → assistant の順序でなければならない**
2. **ToolMessageは標準的なロールではないため、LM Studioが理解できない**
3. **連続した同じロールのメッセージは許可されない**

このプロジェクトのLangGraphワークフローでは：
- HumanMessage (user) → AIMessage (assistant) → ToolMessage → AIMessage のパターンになる
- ToolMessageの後にAIMessageが来るため、LM Studioのテンプレートエラーが発生

## 解決策

### オプション1: OpenAI互換のAPIサービスを使用（推奨）

LM Studioの代わりに、以下のいずれかを使用してください：

#### A. OpenAI公式API
```.env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

#### B. OpenRouter（無料モデルあり）
```.env
OPENAI_API_KEY=sk-or-v1-your-openrouter-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

#### C. Anthropic Claude
```.env
# 別途 langchain-anthropic のインストールが必要
```

### オプション2: LM Studioで利用できるモデルに変更

LM Studioコミュニティでは、より互換性の高いプロンプトテンプレートを持つモデルを提供しています：

1. LM Studioを開く
2. "Discover" タブで `lmstudio-community` を検索
3. 以下のモデルを試す：
   - `lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF`
   - `lmstudio-community/Mistral-7B-Instruct-v0.2-GGUF`

### オプション3: コードを修正してLM Studio専用に最適化

この場合、以下の変更が必要です：

1. **ToolMessageを使わない** - ツールの結果を通常のテキストメッセージに変換
2. **メッセージ履歴を厳密に管理** - user/assistant交互パターンを保証
3. **Function Calling機能を使わない** - 手動で関数を呼び出し、結果をテキストとして返す

これは大幅なコード変更を伴うため、オプション1または2を推奨します。

## 推奨設定

### 開発/テスト用
```env
# OpenRouter の無料モデル（レート制限あり）
OPENAI_API_KEY=sk-or-v1-your-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

### 本番用
```env
# OpenAI公式（安定・高品質）
OPENAI_API_KEY=sk-your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## 現在の .env 設定の問題点

```env
OPENAI_API_KEY=  # 空 → APIキーが必要
OPENAI_API_BASE=http://host.docker.internal:1234/v1  # LM Studio
OPENAI_MODEL=google/gemma-3n-e4b  # Tool Calling非対応
```

**修正が必要：**
- APIキーを設定する（LM Studioでも "dummy-key" などを設定）
- 互換性のあるサービスまたはモデルに変更する

## まとめ

LM Studioでこのプロジェクトを実行するには、モデルの制約により多くの制限があります。

**最も簡単な解決策**: OpenAI APIまたはOpenRouterを使用してください。
