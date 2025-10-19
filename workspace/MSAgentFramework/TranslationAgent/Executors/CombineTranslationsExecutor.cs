using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TranslationAgent.Models;

namespace TranslationAgent.Executors;

/// <summary>
/// 翻訳されたチャンクを結合するExecutor
/// </summary>
public class CombineTranslationsExecutor : ReflectingExecutor<CombineTranslationsExecutor>, IMessageHandler<TranslationState, TranslationState>
{
    /// <summary>
    /// コンストラクタ
    /// </summary>
    public CombineTranslationsExecutor() : base("CombineTranslationsExecutor")
    {
    }

    /// <summary>
    /// メッセージハンドラーの実装
    /// </summary>
    /// <param name="input">入力の翻訳状態</param>
    /// <param name="context">ワークフローコンテキスト</param>
    /// <param name="cancellationToken">キャンセレーショントークン</param>
    /// <returns>更新された翻訳状態</returns>
    public ValueTask<TranslationState> HandleAsync(
        TranslationState input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        Console.WriteLine("[3. ノード実行(combine)] 翻訳結果の結合を開始");

        // 全ての翻訳チャンクを結合
        var finalTranslation = string.Join("\n\n", input.TranslatedChunks);

        Console.WriteLine("[3. ノード完了(combine)] 全ての翻訳を結合完了");

        // 新しい状態を返す
        var newState = new TranslationState
        {
            OriginalText = input.OriginalText,
            TextChunks = input.TextChunks,
            TranslatedChunks = input.TranslatedChunks,
            CurrentIndex = input.CurrentIndex,
            FinalTranslation = finalTranslation
        };

        return ValueTask.FromResult(newState);
    }
}
