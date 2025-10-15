"""
LangGraphを利用した計算機AIエージェント

機能: 自然言語で計算内容を受け取り、四則演算を組み合わせて結果を返す
フロー: 文章解析 → 数式抽出 → 計算実行 → 結果説明

例:
入力: "125と89を足して、その後10を引いてください"
→ 計算式: 125 + 89 - 10
→ 結果: 204
→ 説明: 125と89を足してから10を引くと204になります。
"""

import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# 環境変数の取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# =============================================================================
# 1. ツール定義（四則演算）
# =============================================================================

@tool
def add(a: float, b: float) -> float:
    """2つの数値を加算します。
    
    Args:
        a: 1つ目の数値
        b: 2つ目の数値
    
    Returns:
        a + b の結果
    """
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """2つの数値を減算します。
    
    Args:
        a: 1つ目の数値（被減数）
        b: 2つ目の数値（減数）
    
    Returns:
        a - b の結果
    """
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """2つの数値を乗算します。
    
    Args:
        a: 1つ目の数値
        b: 2つ目の数値
    
    Returns:
        a * b の結果
    """
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """2つの数値を除算します。
    
    Args:
        a: 1つ目の数値（被除数）
        b: 2つ目の数値（除数）
    
    Returns:
        a / b の結果
    
    Raises:
        ValueError: b が 0 の場合
    """
    if b == 0:
        raise ValueError("0で除算することはできません")
    return a / b


# ツールのリスト
tools = [add, subtract, multiply, divide]


# =============================================================================
# 2. 状態定義
# =============================================================================

class AgentState(TypedDict):
    """エージェントの状態を管理する"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_input: str  # ユーザーの入力文
    final_result: float | None  # 最終的な計算結果
    explanation: str  # 結果の説明


# =============================================================================
# 3. ノード定義
# =============================================================================

def parse_and_plan_node(state: AgentState):
    """
    ユーザーの入力を解析して計算プランを立てる
    LLMに計算手順を考えてもらい、ツールを使って実行させる
    """
    messages = state["messages"]
    user_input = state["user_input"]
    
    # LLMの初期化
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE
    )
    llm_with_tools = llm.bind_tools(tools)
    
    # システムプロンプト
    system_message = """あなたは計算を実行するアシスタントです。
ユーザーの自然言語の入力から、必要な計算を段階的に実行してください。

利用可能なツール:
- add(a, b): 加算
- subtract(a, b): 減算
- multiply(a, b): 乗算
- divide(a, b): 除算

計算は複数ステップに分けて実行してください。
例: "125と89を足して、その後10を引く" → まずadd(125, 89)を実行し、その結果をsubtract(結果, 10)で処理
"""
    
    # 新しい計算の場合、システムメッセージを追加
    if len(messages) == 0:
        messages = [
            HumanMessage(content=system_message),
            HumanMessage(content=f"次の計算を実行してください: {user_input}")
        ]
    
    # LLMを呼び出してツール使用を含む応答を取得
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response]
    }


def tool_execution_node(state: AgentState):
    """
    ツールを実行するノード
    LangGraphのToolNodeを使用
    """
    tool_node = ToolNode(tools)
    return tool_node.invoke(state)


def should_continue(state: AgentState) -> str:
    """
    計算を続けるか、説明フェーズに移るかを判断
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # ツール呼び出しがある場合は続行
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    
    # ツール呼び出しがない場合は説明フェーズへ
    return "explain"


def explain_result_node(state: AgentState):
    """
    計算結果を自然言語で説明する
    """
    messages = state["messages"]
    user_input = state["user_input"]
    
    # LLMの初期化
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE
    )
    
    # 最終結果を抽出
    final_result = None
    for message in reversed(messages):
        if hasattr(message, "content") and message.content:
            # ツールの実行結果を探す
            try:
                # ツールメッセージから数値を抽出
                if "ToolMessage" in str(type(message)):
                    final_result = float(message.content)
            except (ValueError, AttributeError):
                continue
    
    # 説明を生成
    explanation_prompt = f"""
ユーザーの入力: "{user_input}"
計算結果: {final_result}

上記の計算プロセスと結果を、わかりやすく自然な日本語で説明してください。
どのような計算を行い、最終的にどのような結果になったかを述べてください。
"""
    
    explanation_message = HumanMessage(content=explanation_prompt)
    explanation_response = llm.invoke([explanation_message])
    
    return {
        "final_result": final_result,
        "explanation": explanation_response.content,
        "messages": [explanation_response]
    }


# =============================================================================
# 4. グラフ構築
# =============================================================================

def create_calculator_graph():
    """計算機エージェントのグラフを作成"""
    
    # グラフの初期化
    workflow = StateGraph(AgentState)
    
    # ノードの追加
    workflow.add_node("parse_and_plan", parse_and_plan_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("explain_result", explain_result_node)
    
    # エントリーポイントの設定
    workflow.set_entry_point("parse_and_plan")
    
    # エッジの追加
    workflow.add_conditional_edges(
        "parse_and_plan",
        should_continue,
        {
            "continue": "tool_execution",
            "explain": "explain_result"
        }
    )
    
    workflow.add_edge("tool_execution", "parse_and_plan")
    workflow.add_edge("explain_result", END)
    
    # グラフのコンパイル
    app = workflow.compile()
    
    return app


# =============================================================================
# 5. メイン実行
# =============================================================================

def run_calculator_agent(user_input: str):
    """
    計算機エージェントを実行
    
    Args:
        user_input: ユーザーからの自然言語での計算依頼
    
    Returns:
        結果の辞書（final_result, explanation）
    """
    # グラフの作成
    app = create_calculator_graph()
    
    # 初期状態
    initial_state = {
        "messages": [],
        "user_input": user_input,
        "final_result": None,
        "explanation": ""
    }
    
    # エージェントの実行
    print(f"\n{'='*60}")
    print(f"入力: {user_input}")
    print(f"{'='*60}\n")

    # 各ステップでの状態遷移を表示
    final_state = None
    for step, state in enumerate(app.stream(initial_state), 1):
        print(f"ステップ {step}: {list(state.keys())[0]}")
        final_state = state
    
    # 最終状態から結果を取得
    result_state = list(final_state.values())[0]
    
    print(f"\n{'======================================'}")
    print(f"結果: {result_state.get('final_result', 'N/A')}")
    print(f"説明: {result_state.get('explanation', 'N/A')}")
    print(f"{'======================================'}\n")
    
    return {
        "final_result": result_state.get("final_result"),
        "explanation": result_state.get("explanation")
    }


if __name__ == "__main__":
    # 環境変数の確認
    if not OPENAI_API_KEY:
        print("エラー: OPENAI_API_KEY が設定されていません")
        print(".env ファイルを作成して以下の設定を追加してください:")
        print("  OPENAI_API_KEY=your-api-key")
        print("  OPENAI_API_BASE=https://api.openai.com/v1")
        print("  OPENAI_MODEL=gpt-4o-mini")
        exit(1)
    
    print(f"使用するモデル: {OPENAI_MODEL}")
    print(f"APIエンドポイント: {OPENAI_API_BASE}")
    print()
    
    # 例の実行
    example_input = "125と89を足して、その後10を引いてください"
    result = run_calculator_agent(example_input)