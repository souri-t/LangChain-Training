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
    
    # 翻訳済みチャンクの数を計算
    translated_count = sum(1 for chunk in state["translated_chunks"] if chunk != "")
    total_chunks = len(state["text_chunks"])
    
    # 翻訳済みの数が総数未満ならチャンク翻訳続行
    if translated_count < total_chunks:
        print("[条件チェック] Next to translate")
        return "translate"

    # 全て翻訳済みなら結合へ
    print("[条件チェック] Next to combine")
    return "combine"
