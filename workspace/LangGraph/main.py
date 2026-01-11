import os
from dotenv import load_dotenv
from translate.translate_agent import Translator

load_dotenv()


def main():
    """翻訳エージェントのメイン処理"""
    # 環境変数のチェック
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    
    if not api_key or not base_url:
        raise EnvironmentError("API_KEY, BASE_URLの環境変数を設定してください。")
    
    # Translatorインスタンスの作成
    translator = Translator(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )
    
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.

    Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving". As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect.

    A machine with artificial general intelligence should be able to solve a wide variety of problems with breadth and versatility similar to human intelligence.
    """
    
    # 翻訳の実行
    result = translator.translate(sample_text)
    print("翻訳結果:")
    print(result)
    
    # グラフ構造の保存（オプション）
    # translator.save_structure("translation_graph_structure.png")


if __name__ == "__main__":
    main()
