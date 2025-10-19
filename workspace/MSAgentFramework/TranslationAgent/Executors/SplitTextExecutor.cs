using System.Text.RegularExpressions;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TranslationAgent.Models;

namespace TranslationAgent.Executors;

/// <summary>
/// テキストを段落ごとに分割するExecutor
/// </summary>
public class SplitTextExecutor : ReflectingExecutor<SplitTextExecutor>, IMessageHandler<TranslationState, TranslationState>
{
    /// <summary>
    /// コンストラクタ
    /// </summary>
    public SplitTextExecutor() : base("SplitTextExecutor")
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
        Console.WriteLine("[1. ノード実行(split)] テキスト分割を開始");

        // テキストを段落ごとに分割（2つ以上の改行で分割）
        var chunks = Regex.Split(input.OriginalText, @"\n\s*\n")
            .Where(chunk => !string.IsNullOrWhiteSpace(chunk))
            .Select(chunk => chunk.Trim())
            .ToList();

        Console.WriteLine($"[1. ノード完了(split)] テキストを{chunks.Count}個のチャンクに分割");

        // 新しい状態を返す
        var newState = new TranslationState
        {
            OriginalText = input.OriginalText,
            TextChunks = chunks,
            TranslatedChunks = Enumerable.Repeat(string.Empty, chunks.Count).ToList(),
            CurrentIndex = 0,
            FinalTranslation = string.Empty
        };

        return ValueTask.FromResult(newState);
    }
}
