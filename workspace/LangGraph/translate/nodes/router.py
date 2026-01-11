from ..state import TranslationState


def should_continue(state: TranslationState) -> str:
    """
    翻訳が完了したかチェック
    
    Args:
        state: 現在の翻訳状態
        
    Returns:
        次のノード名（"translate" または "combine"）
    """
    print("[条件チェック] 翻訳の継続判定")
    
    # 現在のインデックスがチャンク数未満ならチャンク翻訳続行
    if state["current_index"] < len(state["text_chunks"]):
        print("[条件チェック] Next to translate")
        return "translate"

    # 現在のインデックスがチャンク数と等しいなら結合へ
    print("[条件チェック] Next to combine")
    return "combine"
