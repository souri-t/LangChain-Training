from typing import TypedDict, List
from langchain_openai import ChatOpenAI


class TranslationState(TypedDict):
    """翻訳状態を管理する型定義"""
    original_text: str
    text_chunks: List[str]
    translated_chunks: List[str]
    current_index: int
    final_translation: str
    llm: ChatOpenAI
