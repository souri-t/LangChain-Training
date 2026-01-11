from ..state import TranslationState


def translate_chunk(state: TranslationState) -> TranslationState:
    """
    現在のチャンクを翻訳
    
    Args:
        state: 現在の翻訳状態
        
    Returns:
        更新された翻訳状態
    """
    current_idx = state["current_index"]
    total_chunks = len(state["text_chunks"])
    print(f"[2. ノード実行(translate)] チャンク翻訳 ({current_idx + 1}/{total_chunks})")
    
    chunk = state["text_chunks"][current_idx]
    llm = state["llm"]
    
    prompt = f"以下の英文を自然な日本語に翻訳してください。翻訳文のみを出力してください：\n\n{chunk}"
    response = llm.invoke(prompt)
    
    translated_chunks = state["translated_chunks"].copy()
    translated_chunks[current_idx] = response.content

    print(f"[2. ノード完了(translate)] チャンク {current_idx + 1} の翻訳完了")

    return {
        **state,
        "translated_chunks": translated_chunks,
        "current_index": current_idx + 1
    }
