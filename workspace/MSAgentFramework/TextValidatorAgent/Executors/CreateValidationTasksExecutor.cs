using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TextValidatorAgent.Models;

namespace TextValidatorAgent.Executors;

/// <summary>
/// チャンク×チェック観点の組み合わせでタスクキューを生成するExecutor
/// </summary>
public class CreateValidationTasksExecutor : ReflectingExecutor<CreateValidationTasksExecutor>, IMessageHandler<ValidationState, ValidationState>
{
    /// <summary>
    /// コンストラクタ
    /// </summary>
    public CreateValidationTasksExecutor() : base("CreateValidationTasksExecutor")
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
            Console.WriteLine("[2. タスク生成] 処理開始");

            var taskQueue = new Queue<ValidationTask>();

            // チャンク × 観点 のデカルト積でタスクを生成
            for (int i = 0; i < input.TextChunks.Count; i++)
            {
                foreach (var perspective in input.CheckPerspectives)
                {
                    taskQueue.Enqueue(new ValidationTask
                    {
                        ChunkIndex = i,
                        ChunkText = input.TextChunks[i],
                        Perspective = perspective
                    });
                }
            }

            Console.WriteLine($"[2. タスク生成] {taskQueue.Count}個のタスクを生成完了");
            Console.WriteLine($"   - チャンク数: {input.TextChunks.Count}");
            Console.WriteLine($"   - 観点数: {input.CheckPerspectives.Count}");

            // 新しい状態を返す
            var newState = new ValidationState
            {
                OriginalText = input.OriginalText,
                TextChunks = input.TextChunks,
                CheckPerspectives = input.CheckPerspectives,
                TaskQueue = taskQueue,
                Results = input.Results,
                ConsolidatedReport = input.ConsolidatedReport,
                Errors = input.Errors
            };

            return ValueTask.FromResult(newState);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[2. タスク生成] エラー: {ex.Message}");
            var errorState = input;
            errorState.Errors.Add($"タスク生成エラー: {ex.Message}");
            return ValueTask.FromResult(errorState);
        }
    }
}
