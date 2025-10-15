# LangGraph計算機AIエージェント

## 概要
自然言語で計算内容を受け取り、LangGraphのワークフローを使って四則演算を組み合わせて結果を返すAIエージェントです。

## 仕様

### 機能
- 自然言語での計算依頼を解析
- 四則演算（加算、減算、乗算、除算）を組み合わせた計算
- 複数ステップの計算を自動実行
- 結果を自然言語で説明

### フロー
```
文章解析 → 数式抽出 → 計算実行 → 結果説明
```

### 提供ツール
1. **add(a, b)**: 2つの数値を加算
2. **subtract(a, b)**: 2つの数値を減算
3. **multiply(a, b)**: 2つの数値を乗算
4. **divide(a, b)**: 2つの数値を除算

### LangGraphのノード構成
1. **parse_and_plan**: 自然言語を解析して計算プランを立てる
2. **tool_execution**: ツールを呼び出して計算を実行
3. **explain_result**: 最終結果を自然言語で説明

## 使用例

### 入力
```
"125と89を足して、その後10を引いてください"
```

### 処理の流れ
1. 文章解析: "125と89を足す" → "10を引く"
2. 計算実行:
   - `add(125, 89)` → 214
   - `subtract(214, 10)` → 204
3. 結果説明: "125と89を足してから10を引くと204になります。"

### 出力
```
結果: 204
説明: 125と89を足してから10を引くと204になります。
```

## インストール

### 必要なパッケージ
```bash
pip install -r requirements.txt
```

または個別にインストール:
```bash
pip install langchain langchain-openai langgraph python-dotenv
```

### 環境変数の設定

`.env` ファイルを作成して以下の内容を設定してください:

```env
# OpenAI API設定
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

**設定項目:**
- `OPENAI_API_KEY`: OpenAI APIキー（必須）
- `OPENAI_API_BASE`: APIエンドポイント（デフォルト: https://api.openai.com/v1）
- `OPENAI_MODEL`: 使用するモデル名（デフォルト: gpt-4o-mini）

**参考:** `.env.example` ファイルをコピーして使用できます:
```bash
cp .env.example .env
# .env ファイルを編集してAPIキーを設定
```

## 実行方法

```bash
python code.py
```

## コード構造

```
code.py
├── 1. ツール定義（四則演算）
│   ├── add()
│   ├── subtract()
│   ├── multiply()
│   └── divide()
├── 2. 状態定義
│   └── AgentState (TypedDict)
├── 3. ノード定義
│   ├── parse_and_plan_node()
│   ├── tool_execution_node()
│   ├── should_continue()
│   └── explain_result_node()
├── 4. グラフ構築
│   └── create_calculator_graph()
└── 5. メイン実行
    └── run_calculator_agent()
```

## アーキテクチャ

### 状態管理 (AgentState)
- `messages`: メッセージ履歴
- `user_input`: ユーザーの入力文
- `final_result`: 最終的な計算結果
- `explanation`: 結果の説明

### グラフの流れ
```
START
  ↓
parse_and_plan (文章解析・プラン作成)
  ↓
[条件分岐: should_continue]
  ├─ continue → tool_execution (ツール実行) → parse_and_plan (ループ)
  └─ explain → explain_result (結果説明) → END
```

## その他の実行例

### 例1: 複雑な計算
```python
run_calculator_agent("50に30を足して、その結果を2で割ってください")
# 結果: 40.0
# 説明: 50に30を足して80になり、その結果を2で割ると40になります。
```

### 例2: 乗算と加算の組み合わせ
```python
run_calculator_agent("5と8を掛けて、その後20を足してください")
# 結果: 60.0
# 説明: 5と8を掛けて40になり、その後20を足すと60になります。
```

### 例3: 複数ステップ
```python
run_calculator_agent("100から30を引いて、その結果を2で掛けてください")
# 結果: 140.0
# 説明: 100から30を引いて70になり、その結果を2で掛けると140になります。
```

## 注意事項
- OpenAI APIキーが必要です
- ゼロ除算はエラーになります
- LLMの応答により、計算プロセスが異なる場合があります
