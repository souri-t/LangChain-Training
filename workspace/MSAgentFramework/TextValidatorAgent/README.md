# TextValidatorAgent

Microsoft Agent Framework を使用した**ワークフロー型文章レビューエージェント**です。長文の日本語テキストを入力すると、**文章ベースで指定されたチェック依頼を自動的に観点に分解**し、段階的に精査して人間が確認しやすいレビューレポートを生成します。

## 🎯 概要

このエージェントは、単発の応答ではなく、**状態を保持しながら段階的に処理を進めるワークフロー型**の設計になっています。

### 主な特徴

- ✅ **文章ベースのタスク指定**: 自然言語でチェック依頼を記述すると、LLMが自動的に具体的なチェック観点に分解
- ✅ **柔軟なチェック観点**: デフォルトの5観点（誤字・文法・矛盾・用語・曖昧性）に加え、カスタム観点にも対応
- ✅ **段階的処理**: 長文を分割し、タスクキュー方式で効率的にレビュー
- ✅ **状態管理**: Microsoft Agent Framework の `WorkflowBuilder` と条件付きエッジで処理フローを制御
- ✅ **統合レポート**: 各観点のチェック結果を統合し、総合評価を含む最終レポートを生成

## 🔄 ワークフロー構成

```
[ParsePerspectivesText] → [ParseRequest] → [Split] → [CreateTasks] → [Validate] ⟲ → [Consolidate]
         ↓                     ↓              ↓            ↓              ↓             ↓
   観点テキスト解析      依頼解析    テキスト分割   タスク生成    チェック実行   レポート統合
```

### ステップ詳細

1. **ParsePerspectivesTextExecutor** - ユーザーの自然文章形式のチェック観点テキストをLLMで解析し、個別の観点リストに分解
2. **ParseCheckRequestExecutor** - ユーザーの自然言語チェック依頼をLLMで解析し、具体的なチェック観点に分解
3. **SplitTextExecutor** - テキストを段落単位で分割
4. **CreateValidationTasksExecutor** - 分割テキスト × 抽出された観点 のタスクキューを生成
5. **ValidateChunkExecutor** - タスクキューから1件ずつ取り出してLLMでチェック（自己ループで反復）
6. **ConsolidateReportExecutor** - 全結果を統合し、最終レビューレポートを生成

## 📁 プロジェクト構造

```
TextValidatorAgent/
├── Configuration/
│   └── EnvironmentConfig.cs          # 環境変数管理
├── Executors/
│   ├── ParsePerspectivesTextExecutor.cs  # 0A. 観点テキスト解析（NEW）
│   ├── ParseCheckRequestExecutor.cs  # 0B. チェック依頼解析
│   ├── SplitTextExecutor.cs          # 1. テキスト分割
│   ├── CreateValidationTasksExecutor.cs  # 2. タスク生成
│   ├── ValidateChunkExecutor.cs      # 3. チェック実行（LLM呼び出し）
│   └── ConsolidateReportExecutor.cs  # 4. レポート統合（LLM呼び出し）
├── Models/
│   ├── ValidationState.cs            # ワークフロー状態管理
│   ├── ValidationTask.cs             # タスク定義
│   └── ValidationResult.cs           # チェック結果
├── Program.cs                        # メインエントリーポイント
├── TextValidatorAgent.csproj         # プロジェクト設定
└── .env.example                      # 環境変数サンプル
```

## 🚀 セットアップ

### 1. 前提条件

- .NET 8.0 SDK
- OpenAI互換のLLM API（OpenAI、Azure OpenAI、ローカルLLMなど）

### 2. 環境変数の設定

`.env.example` をコピーして `.env` ファイルを作成し、API情報を設定します。

```bash
cd /workspace/MSAgentFramework/TextValidatorAgent
cp .env.example .env
```

`.env` の内容を編集：

```bash
API_KEY=your-api-key-here
BASE_URL=https://your-api-endpoint.com/v1
MODEL_NAME=gpt-4o-mini
```

### 3. パッケージの復元

```bash
export PATH="$HOME/.dotnet:$PATH"
cd /workspace/MSAgentFramework/TextValidatorAgent
dotnet restore
```

### 4. ビルド

```bash
dotnet build
```

### 5. 実行

```bash
dotnet run
```

## 📝 使い方

### チェック依頼の指定方法

**3つの方法**でチェック内容を指定できます。

#### 方法1: 個別の観点を自然文章で指定（推奨）⭐

`Program.cs` の `GetSampleCheckPerspectives()` メソッドで、チェック観点を**自然文章形式**（改行区切り、箇条書き、カンマ区切りなど）で指定できます。

```csharp
static string GetSampleCheckPerspectives()
{
    // パターン1: 改行区切り（推奨）
    return @"日本語表現的な誤りはないか？
番号付きリストを使う場合に各リストは連続しているか？
文章のトーンは一貫しているか？";

    // パターン2: 箇条書き形式
    return @"- 誤字脱字のチェック
- 文法的な誤りの確認
- 論理的な整合性";

    // パターン3: カンマ区切り
    return "トーンの一貫性、専門用語の適切性、読みやすさ";

    // パターン4: 番号付きリスト
    return @"1. 専門用語は正確に使われているか？
2. 段落の構成は論理的か？
3. 読者にとって分かりやすい表現か？";
}
```

**メリット**: 
- 直感的で自然な形式で記述可能
- LLMが自動的に個別の観点に分解
- 複数の記述スタイルに対応

#### 方法2: 自然言語で依頼文を記述

`Program.cs` の `GetSampleCheckRequest()` メソッドで、自然言語でチェック依頼を記述できます。

```csharp
static string GetSampleCheckRequest()
{
    // 例1: 基本的な依頼
    return "この文章の誤字脱字と文法の誤りをチェックしてください。";

    // 例2: ビジネス文書向け
    return "ビジネス文書として適切かどうか、トーンの一貫性、専門用語の使い方、読みやすさをチェックしてください。";
}
```

LLMが依頼文を解析し、適切なチェック観点に自動分解します。

#### 方法3: デフォルト観点を使用

両方とも空にすると、デフォルトの5観点（誤字・文法・矛盾・用語・曖昧性）が使用されます。

```csharp
static string GetSampleCheckPerspectives()
{
    return string.Empty; // 空文字列
}

static string GetSampleCheckRequest()
{
    return string.Empty; // 空文字列
}
```

**優先順位**: 方法1 > 方法2 > 方法3

### サンプルテキストの実行

`Program.cs` の `GetSampleJapaneseText()` メソッドに日本語の長文サンプルが用意されています。`dotnet run` で実行すると、このサンプルテキストがレビューされます。

### カスタムテキストのレビュー

`Program.cs` の `Main` メソッド内で、任意のテキストと観点を指定できます。

```csharp
var sampleText = "あなたの日本語テキストをここに入力...";

// 方法1: 改行区切りで観点を指定（推奨）
var checkPerspectivesText = @"専門用語は正確に使われているか？
段落の構成は論理的か？
読者にとって理解しやすい表現になっているか？";

// または方法2: 自然言語で依頼
var checkRequest = "文章のトーンが一貫しているか、読者に伝わりやすいかをチェックしてください。";
```

## 🧩 チェック観点

### 標準観点（デフォルト）

| 観点キー | 日本語名 | チェック内容 |
|---------|---------|------------|
| `typo` | 誤字・脱字 | 誤字や脱字の検出 |
| `grammar` | 文法的誤り | 助詞の誤り、主述の不一致、時制の問題など |
| `contradiction` | 意味の矛盾 | 論理的な不整合や矛盾の検出 |
| `terminology` | 用語の不統一 | 表記揺れや用語の不統一の検出 |
| `ambiguity` | 表現の曖昧さ | 曖昧で誤解を招く可能性のある表現の検出 |

### 拡張観点

| 観点キー | 日本語名 | チェック内容 |
|---------|---------|------------|
| `tone` | 文章のトーン・文体 | トーンや文体の一貫性チェック |
| `logic` | 論理的整合性 | 論理展開の適切性チェック |
| `readability` | 読みやすさ | 読みやすさの評価 |
| `completeness` | 情報の完全性 | 必要な情報の漏れチェック |
| `accuracy` | 事実の正確性 | 事実関係の誤りチェック |

### カスタム観点

チェック依頼文に含まれる内容から、LLMが自動的に新しい観点を定義することも可能です。

## 🔧 カスタマイズ

### チェック依頼のカスタマイズ

`Program.cs` の `GetSampleCheckRequest()` メソッドで、自然言語でチェック内容を自由に記述できます。

```csharp
// 例：特定の文脈に特化したチェック
return "学術論文として、引用の適切性、論理展開の妥当性、専門用語の正確性をチェックしてください。";
```

### 標準観点の利用

デフォルトの5観点（typo, grammar, contradiction, terminology, ambiguity）を使用する場合は、空文字列を返してください。

### LLMモデルの変更

`.env` ファイルの `MODEL_NAME` を変更するだけで、異なるLLMモデルを使用できます。

## 📊 出力例

### 例1: 改行区切り観点指定の場合

```
=== チェック方法 ===
[観点テキスト指定]
  日本語表現的な誤りはないか？
  番号付きリストを使う場合に各リストは連続しているか？
  文章のトーンは一貫しているか？

[0A. 観点テキスト解析] 処理開始
[0A. 観点テキスト解析] 完了 - 3個の観点を抽出
   - 日本語表現的な誤りはないか？
   - 番号付きリストを使う場合に各リストは連続しているか？
   - 文章のトーンは一貫しているか？

[0B. チェック依頼解析] ユーザー指定の観点を使用 (3個)

[1. テキスト分割] 4個のチャンクに分割完了
[2. タスク生成] 12個のタスクを生成完了
   - チャンク数: 4
   - 観点数: 3

[3. チェック実行] チャンク 1 - 観点: 日本語表現的な誤りはないか？ (残り: 11)
...

=== 文章レビューレポート ===

## 【日本語表現的な誤りはないか？】
...
```

### 例2: 自然言語依頼の場合

```
=== チェック方法 ===
[依頼文] ビジネス文書として適切かどうか、トーンの一貫性、専門用語の使い方、読みやすさをチェックしてください。

[0A. 観点テキスト解析] 観点テキストが空のため、スキップ

[0B. チェック依頼解析] 処理開始
[0B. チェック依頼解析] 完了 - 4個の観点を抽出
   - tone
   - terminology
   - readability
   - business_appropriateness
...
```

## 🛠 技術スタック

- **Microsoft Agent Framework** - ワークフロー制御
- **Microsoft.Extensions.AI** - LLM統合
- **Azure.AI.OpenAI** / **OpenAI SDK** - OpenAI互換API呼び出し
- **.NET 8.0** - ランタイム

## 📖 参考

- [Microsoft Agent Framework Documentation](https://github.com/microsoft/agents)
- [TranslationAgent](../TranslationAgent/) - 同じフレームワークを使用した翻訳エージェントの実装例

## ⚠️ 注意事項

- LLM API の利用にはコストが発生する場合があります
- **チェック依頼の解析で1回 + (チャンク数 × 抽出された観点数) + レポート統合で1回**のLLM呼び出しが発生します
- 長文や多数の観点を指定する場合は、処理時間とコストに注意してください
- エラーハンドリングは基本的な実装のみです。本番環境では追加の例外処理やリトライロジックの実装を推奨します

## 🆕 更新履歴

### v2.2 - 自然文章形式の観点指定対応
- **ParsePerspectivesTextExecutor** を追加し、自然文章形式のチェック観点をLLMで解析・分解
- `UserCheckPerspectivesText` フィールドを `ValidationState` に追加
- 改行区切り、箇条書き、カンマ区切り、番号付きリストなど多様な入力形式に対応
- ワークフローに観点テキスト解析ステップを追加（ParsePerspectivesText → ParseRequest → ...）
- `GetSampleCheckPerspectives()` を文字列を返すメソッドに変更し、より自然な記述が可能に

### v2.1 - 個別観点の文字列指定機能追加
- **UserCheckPerspectives** フィールドを `ValidationState` に追加
- チェック観点を文字列リストで直接指定可能に（方法1として推奨）
- 観点指定の優先順位を実装（個別観点 > 自然言語依頼 > デフォルト）
- `GetSampleCheckPerspectives()` メソッドを追加し、使用例を提供

### v2.0 - 文章ベースタスク分解機能追加
- **ParseCheckRequestExecutor** を追加し、自然言語でのチェック依頼に対応
- 標準観点を5個から10個に拡張（tone, logic, readability, completeness, accuracy を追加）
- カスタム観点の動的生成に対応
- ワークフローに依頼解析ステップを追加（ParseRequest → Split → CreateTasks → Validate → Consolidate）

### v1.0 - 初版リリース
- 基本的なワークフロー型文章レビュー機能

## 📜 ライセンス

このプロジェクトは MIT License のもとで公開されています。
