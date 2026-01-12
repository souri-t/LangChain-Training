"""
用語集用ツール定義

"""

from typing import Dict
from langchain_core.tools import tool


@tool
def get_glossary() -> Dict[str, str]:
    """日英専門用語辞書を取得します。
    
    Returns:
        用語リストを含む辞書（英語: 日本語）
    """
    # 専門用語辞書（全分野統合）
    glossary = {
        # IT / テクノロジー
        "API": "アプリケーションプログラミングインターフェース（API）",
        "HTTP": "ハイパーテキスト転送プロトコル（HTTP）",
        "algorithm": "アルゴリズム",
        "database": "データベース",
        "server": "サーバー",
        "cloud": "クラウド",
        "AI": "人工知能（AI）",
        "machine learning": "機械学習",
        "neural network": "ニューラルネットワーク",
        "GPU": "グラフィックス処理装置（GPU）",
        "CPU": "中央処理装置（CPU）",
        "framework": "フレームワーク",
        "library": "ライブラリ",
        "protocol": "プロトコル",
        "software": "ソフトウェア",
        "intelligent agents": "知的エージェント",
        "cognitive": "認知的",
        "artificial general intelligence": "汎用人工知能（AGI）",
        "deep learning": "深層学習",
        "parallel processing": "並列処理",
        
        # 医療
        "diagnosis": "診断",
        "treatment": "治療",
        "patient": "患者",
        "clinical": "臨床の",
        "disease": "疾患",
        "symptom": "症状",
        "therapy": "療法",
        "pharmaceutical": "医薬品",
        
        # 法律
        "contract": "契約",
        "lawsuit": "訴訟",
        "plaintiff": "原告",
        "defendant": "被告",
        "attorney": "弁護士",
        "litigation": "訴訟",
        "jurisdiction": "管轄権",
        "statute": "法令",
        
        # 金融
        "investment": "投資",
        "portfolio": "ポートフォリオ",
        "securities": "証券",
        "equity": "株式",
        "dividend": "配当",
        "bond": "債券",
        "asset": "資産",
        "liability": "負債"
    }
    
    return glossary

