from typing import TypedDict, List
from langchain_openai import ChatOpenAI


class TranslationState(TypedDict):
    """翻訳状態を管理する型定義"""
    original_text: str  # 翻訳元の原文テキスト
    text_chunks: List[str]  # 段落ごとに分割されたテキストのリスト
    translated_chunks: List[str]  # 翻訳済みチャンクのリスト（未翻訳は空文字列）
    final_translation: str  # 最終的な翻訳結果（全チャンクを結合したもの）
    llm: ChatOpenAI  # 翻訳に使用するLLMインスタンス
