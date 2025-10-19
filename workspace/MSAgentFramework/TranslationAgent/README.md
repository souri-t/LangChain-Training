# Translation Agent - Microsoft Agent Framework版

このプロジェクトは、LangGraphで実装された翻訳エージェントをMicrosoft Agent Frameworkで再実装したものです。

## 概要

長文の英文を日本語に翻訳するAIエージェントです。テキストを段落ごとに分割し、各チャンクを順次翻訳してから結合することで、効率的に長文翻訳を実現します。

## ワークフロー構造

1. **テキスト分割 (split)**: 入力テキストを段落ごとに分割
2. **チャンク翻訳 (translate)**: 各チャンクをAIで翻訳（ループ処理）
3. **結合 (combine)**: 翻訳されたチャンクを一つの文書に結合

## 技術スタック

- .NET 8
- Microsoft Agent Framework (Workflows)
- Azure OpenAI / OpenAI互換API

## セットアップ

1. `.env.example`を`.env`にコピーして、環境変数を設定:
   ```bash
   cp .env.example .env
   ```

2. `.env`ファイルを編集して、APIキーとエンドポイントを設定:
   ```
   API_KEY=your-actual-api-key
   BASE_URL=https://your-api-endpoint.com/v1
   MODEL_NAME=gpt-4o-mini
   ```

## 実行方法

```bash
dotnet run
```

## プロジェクト構造

- `Program.cs`: メインエントリーポイント
- `TranslationState.cs`: ワークフローの状態定義
- `Executors/`: 各処理を実行するExecutorクラス群
  - `SplitTextExecutor.cs`: テキスト分割
  - `TranslateChunkExecutor.cs`: チャンク翻訳
  - `CombineTranslationsExecutor.cs`: 翻訳結合
- `Configuration/`: 環境変数読み込み

## LangGraph版との対応

| LangGraph | Microsoft Agent Framework |
|-----------|---------------------------|
| StateGraph | WorkflowBuilder |
| ノード関数 | IMessageHandler実装Executor |
| 条件付きエッジ | AddConditionalEdges |
| ChatOpenAI | ChatClient (OpenAI) |

## ライセンス

このプロジェクトはオリジナルのLangGraph版と同じ仕様で実装されています。
