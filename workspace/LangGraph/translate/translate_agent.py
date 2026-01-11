from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .state import TranslationState
from .nodes import split_text, translate_chunk, combine_translations, should_continue


class Translator:
    """LangGraphを使用した長文翻訳エージェント"""
    
    def __init__(self, api_key: str, base_url: str, model_name: str = "gpt-4o-mini", temperature: float = 0):
        """
        Translatorの初期化
        
        Args:
            api_key: OpenAI APIキー
            base_url: APIのベースURL
            model_name: 使用するモデル名（デフォルト: gpt-4o-mini）
            temperature: モデルの温度パラメータ（デフォルト: 0）
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self._llm = None
    
    @property
    def llm(self) -> ChatOpenAI:
        """LLMインスタンスの遅延初期化"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self.temperature
            )
        return self._llm
    
    def create_translation_graph_app(self):
        """
        翻訳グラフを作成
        
        Returns:
            コンパイル済みのLangGraphアプリケーション
        """
        workflow = StateGraph(TranslationState)
        
        # ノードの追加
        workflow.add_node("split", split_text)
        workflow.add_node("translate", translate_chunk)
        workflow.add_node("combine", combine_translations)

        # エッジの追加
        workflow.set_entry_point("split")
        workflow.add_edge("split", "translate")
        workflow.add_conditional_edges("translate", should_continue, {
            "translate": "translate",
            "combine": "combine"
        })
        workflow.add_edge("combine", END)
        
        # グラフのコンパイル
        app = workflow.compile()
        
        return app
    
    def translate(self, text: str) -> str:
        """
        長文テキストを翻訳
        
        Args:
            text: 翻訳対象のテキスト
            
        Returns:
            翻訳されたテキスト
        """
        app = self.create_translation_graph_app()
        
        initial_state = {
            "original_text": text,
            "text_chunks": [],
            "translated_chunks": [],
            "current_index": 0,
            "final_translation": "",
            "llm": self.llm
        }
        
        result = app.invoke(initial_state)
        return result["final_translation"]
    
    def save_structure(self, file_path: str = "graph_structure.png"):
        """
        グラフ構造を画像として保存
        
        Args:
            file_path: 保存先のファイルパス（デフォルト: graph_structure.png）
        """
        app = self.create_translation_graph_app()
        if not app:
            return
        with open(file_path, "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
