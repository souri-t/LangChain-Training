import re
from ..state import TranslationState


def split_text(state: TranslationState) -> TranslationState:
    """
    テキストを段落ごとに分割
    
    Args:
        state: 現在の翻訳状態
        
    Returns:
        更新された翻訳状態
    """
    print("[1. ノード実行(split)] テキスト分割を開始")
    text = state["original_text"]
    chunks = [chunk.strip() for chunk in re.split(r'\n\s*\n', text) if chunk.strip()]
    print(f"[1. ノード完了(split)] テキストを{len(chunks)}個のチャンクに分割")

    return {
        **state,
        "text_chunks": chunks,
        "translated_chunks": [""] * len(chunks)
    }
