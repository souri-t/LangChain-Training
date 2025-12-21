"""
PowerPoint操作用ツール定義

PowerPointファイルの読み込み、テキスト抽出、翻訳、書き込みを行うツール群
"""

from typing import Dict, Any, List
from langchain_core.tools import tool
from pptx import Presentation


@tool
def load_pptx(file_path: str) -> Dict[str, Any]:
    """PowerPointファイルを読み込み、スライド情報を抽出します。
    
    Args:
        file_path: PowerPointファイルのパス
    
    Returns:
        スライド情報を含む辞書 (slide_count, file_path)
    """
    try:
        prs = Presentation(file_path)
        return {
            "slide_count": len(prs.slides),
            "file_path": file_path,
            "success": True
        }
    except Exception as e:
        return {
            "slide_count": 0,
            "file_path": file_path,
            "success": False,
            "error": str(e)
        }


@tool
def extract_text_from_slide(file_path: str, slide_index: int) -> Dict[str, Any]:
    """指定されたスライドからテキストを抽出します。
    
    Args:
        file_path: PowerPointファイルのパス
        slide_index: スライドのインデックス（0始まり）
    
    Returns:
        抽出されたテキスト情報を含む辞書
    """
    try:
        prs = Presentation(file_path)
        slide = prs.slides[slide_index]
        
        texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                texts.append({
                    "text": shape.text,
                    "shape_id": shape.shape_id
                })
        
        return {
            "slide_index": slide_index,
            "texts": texts,
            "text_count": len(texts),
            "success": True
        }
    except Exception as e:
        return {
            "slide_index": slide_index,
            "texts": [],
            "text_count": 0,
            "success": False,
            "error": str(e)
        }


@tool
def translate_text(text: str, source_lang: str = "Japanese", target_lang: str = "English") -> str:
    """テキストを翻訳します。
    
    Args:
        text: 翻訳対象のテキスト
        source_lang: 元の言語
        target_lang: 翻訳先の言語
    
    Returns:
        翻訳されたテキスト
    """
    # この関数は実際にはLLMノードで使用されるため、
    # ここではプレースホルダーとして機能します
    return text


@tool
def update_slide_text(file_path: str, slide_index: int, translations: List[Dict[str, str]]) -> Dict[str, Any]:
    """スライドのテキストを翻訳結果で更新します。
    
    Args:
        file_path: PowerPointファイルのパス
        slide_index: スライドのインデックス
        translations: 翻訳結果のリスト [{shape_id: ..., original: ..., translated: ...}, ...]
    
    Returns:
        更新結果を含む辞書
    """
    try:
        prs = Presentation(file_path)
        slide = prs.slides[slide_index]
        
        updated_count = 0
        for shape in slide.shapes:
            if hasattr(shape, "text_frame"):
                for trans in translations:
                    if trans.get("shape_id") == shape.shape_id:
                        # テキストフレームの内容を翻訳結果で置き換え
                        if shape.text_frame.text == trans.get("original"):
                            shape.text_frame.text = trans.get("translated")
                            updated_count += 1
        
        # ファイルを保存
        prs.save(file_path)
        
        return {
            "slide_index": slide_index,
            "updated_count": updated_count,
            "success": True
        }
    except Exception as e:
        return {
            "slide_index": slide_index,
            "updated_count": 0,
            "success": False,
            "error": str(e)
        }


# ツールのリスト
tools = [load_pptx, extract_text_from_slide, translate_text, update_slide_text]
