
"""
PDFファイルからテキスト抽出を行うユーティリティ関数群。
"""

from PyPDF2 import PdfReader

def extract_text_from_pdf(file) -> str:
    """
    PDFファイルからテキストを抽出する関数。
    Args:
        file: Streamlitのアップロードファイルまたはファイルオブジェクト
    Returns:
        str: 抽出されたテキスト全文
    """
    reader = PdfReader(file)
    text = "\n".join([page.extract_text() or '' for page in reader.pages])
    return text
