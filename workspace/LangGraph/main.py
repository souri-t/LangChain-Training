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
        
    # グラフ構造の保存（オプション）
    translator.save_structure("translation_graph_structure.png")

    # 専門用語を含むサンプルテキスト（AI/機械学習分野）
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.

    Machine learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. Neural networks, which are inspired by biological neural networks, form the foundation of deep learning algorithms.

    Modern AI systems utilize GPUs for parallel processing of complex algorithms. Cloud computing platforms provide the necessary infrastructure for training large-scale neural networks. These systems often employ HTTP APIs for integration with other software components.

    A machine with artificial general intelligence (AGI) should be able to solve a wide variety of problems with breadth and versatility similar to human intelligence. Current research focuses on improving the cognitive capabilities of AI systems.
    """
    
    # 翻訳の実行
    result = translator.translate(sample_text)
    print("翻訳結果:")
    print(result)


if __name__ == "__main__":
    main()
