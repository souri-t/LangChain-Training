from ..state import TranslationState
from ..tools.glossary import get_glossary


def analyze_terminology(state: TranslationState) -> TranslationState:
    """
    LLMを使って各チャンクから専門用語を抽出し、辞書と照合
    
    各チャンクに対してLLMで専門用語を抽出し、
    get_glossaryツールで取得した辞書と照合して
    該当する用語の翻訳を取得する
    
    Args:
        state: 現在の翻訳状態
        
    Returns:
        detected_termsを含む更新された状態
    """
    print("[専門用語分析] LLMによる専門用語の抽出と照合を開始")
    
    text_chunks = state["text_chunks"]
    llm = state["llm"]
    detected_terms = []
    
    # 辞書から用語リストを取得
    glossary_dict = get_glossary.invoke({})
    
    print(f"[専門用語分析] {len(glossary_dict)}件の用語辞書を読み込みました")
    
    for idx, chunk in enumerate(text_chunks):
        # LLMで専門用語を抽出
        prompt = f"""以下のテキストから専門用語（技術用語、医学用語、法律用語、金融用語など）を抽出してください。

テキスト:
{chunk}

指示:
1. テキスト中に含まれる専門用語をカンマ区切りで列挙してください
2. 一般的な単語ではなく、専門的・技術的な用語のみを抽出してください
3. 専門用語が含まれていない場合は "NONE" と答えてください
4. 用語のみを出力してください（説明は不要）

専門用語:"""

        response = llm.invoke(prompt)
        extracted_text = response.content.strip()
        
        # 抽出された用語を解析
        chunk_terms = {}
        if extracted_text.upper() != "NONE":
            # カンマ区切りで分割して各用語を処理
            terms = [term.strip() for term in extracted_text.split(",")]
            
            # 辞書と照合
            for term in terms:
                # 完全一致
                if term in glossary_dict:
                    chunk_terms[term] = glossary_dict[term]
                # 小文字で完全一致
                elif term.lower() in glossary_dict:
                    chunk_terms[term] = glossary_dict[term.lower()]
                # 部分一致（辞書のキーに含まれるか）
                else:
                    for dict_term, translation in glossary_dict.items():
                        if term.lower() in dict_term.lower() or dict_term.lower() in term.lower():
                            chunk_terms[term] = translation
                            break
        
        detected_terms.append(chunk_terms)
        
        if chunk_terms:
            print(f"[専門用語分析] チャンク {idx + 1}/{len(text_chunks)}: {len(chunk_terms)}件の専門用語を検出")
            sample_terms = list(chunk_terms.items())[:3]
            for en, ja in sample_terms:
                print(f"  - {en}: {ja}")
        else:
            print(f"[専門用語分析] チャンク {idx + 1}/{len(text_chunks)}: 専門用語なし")
    
    total_chunks_with_terms = sum(1 for terms in detected_terms if terms)
    print(f"[専門用語分析] 分析完了: {total_chunks_with_terms}/{len(text_chunks)} チャンクに専門用語が含まれています")
    
    return {
        **state,
        "detected_terms": detected_terms
    }
