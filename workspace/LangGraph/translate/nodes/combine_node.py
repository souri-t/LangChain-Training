from ..state import TranslationState


def combine_translations(state: TranslationState) -> TranslationState:
    """
    翻訳されたチャンクを結合
    
    Args:
        state: 現在の翻訳状態
        
    Returns:
        更新された翻訳状態
    """
    print("[3. ノード実行(combine)] 翻訳結果の結合を開始")
    final_translation = "\n\n".join(state["translated_chunks"])
    print("[3. ノード完了(combine)] 全ての翻訳を結合完了")

    return {
        **state,
        "final_translation": final_translation
    }
