# LangGraph 長文翻訳AIエージェント

英文の長文を日本語に翻訳するLangGraphベースのAIエージェントです。

## セットアップ

1. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数を設定:
```bash
cp .env.example .env
# .envファイルにAPI設定を記入
# OpenRouter使用時: API_KEY, BASE_URL, MODEL_NAMEを設定
```

## 使用方法

```python
from translation_agent import translate_long_text

text = "Your long English text here..."
result = translate_long_text(text)
print(result)
```

## 実行

```bash
python translation_agent.py
```