from ..state import TranslationState


def translate_chunk(state: TranslationState) -> TranslationState:
    """
    現在のチャンクを翻訳（専門用語を考慮）
    
    検出された専門用語がある場合、それをプロンプトに含めて
    翻訳の一貫性と精度を向上させる
    
    Args:
        state: 現在の翻訳状態
        
    Returns:
        更新された翻訳状態
    """
    # 翻訳済みチャンクの数から現在のインデックスを計算
    translated_chunks = state["translated_chunks"]
    current_idx = sum(1 for chunk in translated_chunks if chunk != "")
    total_chunks = len(state["text_chunks"])
    
    chunk = state["text_chunks"][current_idx]
    llm = state["llm"]
    detected_terms = state.get("detected_terms", [])
    
    # このチャンクで検出された専門用語を取得
    chunk_terms = detected_terms[current_idx] if current_idx < len(detected_terms) else {}
    
    if chunk_terms:
        print(f"[翻訳(専門用語考慮)] チャンク {current_idx + 1}/{total_chunks}")
        
        # 専門用語辞書をプロンプトに組み込む
        terms_context = "\n".join([f"- {en}: {ja}" for en, ja in chunk_terms.items()])
        
        prompt = f"""以下の英文を自然な日本語に翻訳してください。

専門用語の対訳表:
{terms_context}

重要な注意事項:
1. 上記の専門用語が文中に出現した場合、対訳表の訳語を使用してください
2. 専門用語の一貫性を保ってください
3. 文脈に応じて自然な日本語になるように調整してください
4. 翻訳文のみを出力してください

翻訳対象テキスト:
{chunk}"""
    else:
        print(f"[翻訳(通常)] チャンク {current_idx + 1}/{total_chunks}")
        prompt = f"以下の英文を自然な日本語に翻訳してください。翻訳文のみを出力してください：\n\n{chunk}"
    
    response = llm.invoke(prompt)
    
    new_translated_chunks = translated_chunks.copy()
    new_translated_chunks[current_idx] = response.content

    print(f"[翻訳完了] チャンク {current_idx + 1} の翻訳完了")

    return {
        **state,
        "translated_chunks": new_translated_chunks
    }
