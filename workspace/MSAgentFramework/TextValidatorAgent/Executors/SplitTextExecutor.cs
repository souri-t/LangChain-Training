using System.Text.RegularExpressions;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TextValidatorAgent.Models;

namespace TextValidatorAgent.Executors;

/// <summary>
/// テキストを段落ごとに分割するExecutor
/// </summary>
public class SplitTextExecutor : ReflectingExecutor<SplitTextExecutor>, IMessageHandler<ValidationState, ValidationState>
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
    /// <param name="input">入力の検証状態</param>
    /// <param name="context">ワークフローコンテキスト</param>
    /// <param name="cancellationToken">キャンセレーショントークン</param>
    /// <returns>更新された検証状態</returns>
    public ValueTask<ValidationState> HandleAsync(
        ValidationState input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            Console.WriteLine("[1. テキスト分割] 処理開始");

            // テキストを段落ごとに分割（2つ以上の改行で分割）
            var chunks = Regex.Split(input.OriginalText, @"\n\s*\n")
                .Where(chunk => !string.IsNullOrWhiteSpace(chunk))
                .Select(chunk => chunk.Trim())
                .ToList();

            Console.WriteLine($"[1. テキスト分割] {chunks.Count}個のチャンクに分割完了");

            // 新しい状態を返す
            var newState = new ValidationState
            {
                OriginalText = input.OriginalText,
                TextChunks = chunks,
                CheckPerspectives = input.CheckPerspectives,
                TaskQueue = new Queue<ValidationTask>(),
                Results = new List<ValidationResult>(),
                ConsolidatedReport = string.Empty,
                Errors = new List<string>()
            };

            return ValueTask.FromResult(newState);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[1. テキスト分割] エラー: {ex.Message}");
            var errorState = new ValidationState
            {
                OriginalText = input.OriginalText,
                Errors = new List<string> { $"分割処理エラー: {ex.Message}" }
            };
            return ValueTask.FromResult(errorState);
        }
    }
}
