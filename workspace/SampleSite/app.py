import streamlit as st
from diff_match_patch import diff_match_patch
import os
import json
from typing import List, Tuple
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


def calculate_diff(text1: str, text2: str):
    """2つのテキスト間の差分を計算"""
    dmp = diff_match_patch()
    diffs = dmp.diff_main(text1, text2)
    dmp.diff_cleanupSemantic(diffs)
    return diffs


def calculate_diff_with_llm(text1: str, text2: str) -> List[Tuple[int, str]]:
    """OpenAI互換のLLMを使って2つのテキスト間の差分を計算
    
    Args:
        text1: 元のテキスト
        text2: 新しいテキスト
        
    Returns:
        diff_match_patchと同じ形式のリスト: List[Tuple[int, str]]
        各タプルは (操作コード, テキスト) で、操作コードは:
        -1: 削除, 0: 変更なし, 1: 追加
    """
    try:
        from openai import OpenAI
        
        # OpenAI互換のAPIエンドポイントとAPIキーを環境変数から取得
        api_key = os.getenv("OPENAI_API_KEY", "")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        if not api_key:
            st.error("OPENAI_API_KEYが設定されていません。環境変数を設定してください。")
            return [(0, text1)]
        
        client = OpenAI(api_key=api_key, base_url=api_base)
        
        prompt = f"""以下の2つのテキストを文字レベル・単語レベルで詳細に比較し、差分を分析してください。

**重要な指示:**
1. 可能な限り細かい粒度で差分を検出してください（文字レベル、単語レベル）
2. 長い共通部分は細かく分割せず、まとめて出力してください
3. 変更がある部分の前後は、単語や文節単位で細かく区切ってください
4. 空白や改行も正確に含めてください

**出力形式（JSON）:**
{{
  "diffs": [
    {{"op": 0, "text": "共通の長い部分"}},
    {{"op": -1, "text": "削除された単語"}},
    {{"op": 1, "text": "追加された単語"}},
    {{"op": 0, "text": "の"}},
    {{"op": 0, "text": "共通部分"}},
    ...
  ]
}}

**opの意味:**
- -1: text1から削除された部分
- 0: 両方に共通する変更なしの部分
- 1: text2に追加された部分

**例:**
テキスト1: "これは元の文章です。"
テキスト2: "これは新しい文章です。"

期待される出力:
{{
  "diffs": [
    {{"op": 0, "text": "これは"}},
    {{"op": -1, "text": "元"}},
    {{"op": 1, "text": "新しい"}},
    {{"op": 0, "text": "の文章です。"}}
  ]
}}

**分析対象:**

テキスト1（元のテキスト）:
```
{text1}
```

テキスト2（新しいテキスト）:
```
{text2}
```

JSONのみを返してください。説明は不要です。細かく分割することを忘れないでください。"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "あなたはテキストの差分を文字レベル・単語レベルで詳細に分析する専門家です。diff-match-patchアルゴリズムと同等の細かい粒度で差分を抽出します。変更がある部分は特に細かく分割し、共通部分でも変更箇所の前後は単語単位で区切ります。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # JSONから差分リストを構築
        diffs = []
        for diff_item in result_json.get("diffs", []):
            op = diff_item.get("op", 0)
            text = diff_item.get("text", "")
            diffs.append((op, text))
        
        return diffs if diffs else [(0, text1)]
        
    except ImportError:
        st.error("openaiライブラリがインストールされていません。`pip install openai`を実行してください。")
        return [(0, text1)]
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            st.error("⚠️ レート制限エラーが発生しました")
            st.warning(f"""
            **原因:** モデルが一時的にレート制限されています。
            
            **対処方法:**
            1. 数分待ってから再度試す
            2. 別の無料モデルに変更する（.envファイル）:
               - `meta-llama/llama-3.2-3b-instruct:free`
               - `google/gemma-2-9b-it:free`
               - `qwen/qwen-2-7b-instruct:free`
            3. 有料モデルを使用する（より安定）
            
            **詳細:** {error_msg}
            """)
        else:
            st.error(f"LLMでの差分計算中にエラーが発生しました: {error_msg}")
        # エラー時は元のテキストをそのまま返す
        return [(0, text1)]


def render_diff_html(diffs):
    """差分をHTMLで色付けして表示"""
    html_parts = []
    
    for op, text in diffs:
        # HTML特殊文字をエスケープ
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # 改行を<br>に変換
        text = text.replace('\n', '<br>')
        
        if op == -1:  # 削除
            html_parts.append(f'<span style="background-color: #ffcccc; text-decoration: line-through;">{text}</span>')
        elif op == 1:  # 追加
            html_parts.append(f'<span style="background-color: #ccffcc;">{text}</span>')
        else:  # 変更なし
            html_parts.append(f'<span>{text}</span>')
    
    return ''.join(html_parts)


def main():
    st.set_page_config(
        page_title="テキスト差分比較ツール",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 テキスト差分比較ツール")
    st.markdown("2つのテキストを比較して、差分を視覚的に表示します。")
    st.markdown("---")
    
    # 2カラムレイアウト
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("テキスト1（元の文章）")
        text1 = st.text_area(
            "テキスト1を入力してください",
            value="これは元の文章です。\nこの部分は変更されません。\nこの行は削除されます。",
            height=300,
            key="text1"
        )
    
    with col2:
        st.subheader("テキスト2（新しい文章）")
        text2 = st.text_area(
            "テキスト2を入力してください",
            value="これは新しい文章です。\nこの部分は変更されません。\nこの行が追加されました。",
            height=300,
            key="text2"
        )
    
    st.markdown("---")
    
    # 差分計算方法の選択
    diff_method = st.radio(
        "差分計算方法を選択",
        ["diff-match-patch（高速）", "LLM（AI分析）"],
        horizontal=True
    )
    
    # 比較ボタン
    if st.button("差分を比較", type="primary", use_container_width=True):
        if text1 or text2:
            with st.spinner("差分を計算中..."):
                if diff_method == "diff-match-patch（高速）":
                    diffs = calculate_diff(text1, text2)
                else:  # LLM
                    diffs = calculate_diff_with_llm(text1, text2)
                
                st.subheader("📊 差分結果")
                
                # 統計情報
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                deletions = sum(1 for op, _ in diffs if op == -1)
                additions = sum(1 for op, _ in diffs if op == 1)
                unchanged = sum(1 for op, _ in diffs if op == 0)
                
                with stats_col1:
                    st.metric("削除", deletions)
                with stats_col2:
                    st.metric("追加", additions)
                with stats_col3:
                    st.metric("変更なし", unchanged)
                
                st.markdown("---")
                
                # 差分の表示
                st.markdown("### 差分の詳細")
                st.markdown("**凡例:** <span style='background-color: #ffcccc;'>赤＝削除</span> | "
                          "<span style='background-color: #ccffcc;'>緑＝追加</span> | "
                          "<span>灰色＝変更なし</span>",
                          unsafe_allow_html=True)
                
                html_diff = render_diff_html(diffs)
                st.markdown(
                    f'<div style="padding: 20px; border: 1px solid #ddd; border-radius: 5px; '
                    f'background-color: #f9f9f9; line-height: 1.8; font-family: monospace;">'
                    f'{html_diff}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("少なくとも1つのテキストを入力してください。")
    
    # サイドバーに説明を追加
    with st.sidebar:
        st.header("使い方")
        st.markdown("""
        1. **テキスト1**に元の文章を入力
        2. **テキスト2**に新しい文章を入力
        3. **差分を比較**ボタンをクリック
        
        ### 差分の見方
        - 🔴 **赤色（取り消し線）**: テキスト1から削除された部分
        - 🟢 **緑色**: テキスト2に追加された部分
        - ⚪ **通常表示**: 変更がない部分
        
        ### ヒント
        - 長い文章でも比較できます
        - 改行も差分として検出されます
        - 統計情報で変更の概要を確認できます
        """)
        
        st.markdown("---")
        st.markdown("**Powered by**")
        st.markdown("- Streamlit")
        st.markdown("- diff-match-patch")


if __name__ == "__main__":
    main()
