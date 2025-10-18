from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import re
import os
from dotenv import load_dotenv

load_dotenv()

def save_structure(app, file_path: str = "graph_structure.png"):
    """グラフ構造を保存する"""
    if not app:
        return
    with open(file_path, "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())

class TranslationState(TypedDict):
    original_text: str
    text_chunks: List[str]
    translated_chunks: List[str]
    current_index: int
    final_translation: str

def split_text(state: TranslationState) -> TranslationState:
    """テキストを段落ごとに分割"""
    print("[1. ノード実行(split)] テキスト分割を開始")
    text = state["original_text"]
    chunks = [chunk.strip() for chunk in re.split(r'\n\s*\n', text) if chunk.strip()]
    print(f"[1. ノード完了(split)] テキストを{len(chunks)}個のチャンクに分割")

    return {
        **state,
        "text_chunks": chunks,
        "translated_chunks": [""] * len(chunks),
        "current_index": 0
    }

def translate_chunk(state: TranslationState) -> TranslationState:
    """現在のチャンクを翻訳"""
    current_idx = state["current_index"]
    total_chunks = len(state["text_chunks"])
    print(f"[2. ノード実行(translate)] チャンク翻訳 ({current_idx + 1}/{total_chunks})")

    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        temperature=0
    )
    
    chunk = state["text_chunks"][current_idx]
    
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

def combine_translations(state: TranslationState) -> TranslationState:
    """翻訳されたチャンクを結合"""
    print("[3. ノード実行(combine)] 翻訳結果の結合を開始")
    final_translation = "\n\n".join(state["translated_chunks"])
    print("[3. ノード完了(combine)] 全ての翻訳を結合完了")

    return {
        **state,
        "final_translation": final_translation
    }

def should_continue(state: TranslationState) -> str:
    """翻訳が完了したかチェック"""
    print("[条件チェック] 翻訳の継続判定")
    
    # 現在のインデックスがチャンク数未満ならチャンク翻訳続行
    if state["current_index"] < len(state["text_chunks"]):
        print("[条件チェック] Next to translate")
        return "translate"

    # 現在のインデックスがチャンク数と等しいなら結合へ
    print("[条件チェック] Next to combine")
    return "combine"

def create_translation_graph_app():
    """翻訳グラフを作成"""
    workflow = StateGraph(TranslationState)
    
    # ノードの追加
    workflow.add_node("split", split_text)  ## テキスト分割ノード
    workflow.add_node("translate", translate_chunk) ## チャンク翻訳ノード
    workflow.add_node("combine", combine_translations) ## 結合ノード

    # エッジの追加
    
    ## 開始エッジ
    workflow.set_entry_point("split")
    
    ## 直線エッジ
    workflow.add_edge("split", "translate")
    
    ## 条件付きエッジ
    workflow.add_conditional_edges("translate", should_continue, {
        "translate": "translate",
        "combine": "combine"
    })
    
    ## 最終エッジ
    workflow.add_edge("combine", END)
    
    # グラフのコンパイル
    app = workflow.compile()
    
    return app

def translate_long_text(text: str) -> str:
    """長文翻訳のメイン関数"""
    app = create_translation_graph_app()
    
    # appのワークフローのMermaidをpngで保存する
    # save_structure(app, "translation_graph_structure.png")
    
    initial_state = {
        "original_text": text,
        "text_chunks": [],
        "translated_chunks": [],
        "current_index": 0,
        "final_translation": ""
    }
    
    result = app.invoke(initial_state)
    return result["final_translation"]

if __name__ == "__main__":
    
    # 環境変数のチェック
    if not os.getenv("API_KEY") or not os.getenv("BASE_URL") or not os.getenv("MODEL_NAME"):
        raise EnvironmentError("API_KEY, BASE_URL, MODEL_NAMEの環境変数を設定してください。")
    
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.

    Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving". As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect.

    A machine with artificial general intelligence should be able to solve a wide variety of problems with breadth and versatility similar to human intelligence.
    """
    
    result = translate_long_text(sample_text)
    print("翻訳結果:")
    print(result)