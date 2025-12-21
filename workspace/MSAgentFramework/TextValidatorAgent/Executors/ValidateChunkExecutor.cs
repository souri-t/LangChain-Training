using Microsoft.Extensions.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TextValidatorAgent.Models;

namespace TextValidatorAgent.Executors;

/// <summary>
/// タスクキューから1件取り出してチェックを実行するExecutor
/// </summary>
public class ValidateChunkExecutor : ReflectingExecutor<ValidateChunkExecutor>, IMessageHandler<ValidationState, ValidationState>
{
    /// <summary>
    /// チャットクライアント
    /// </summary>
    private readonly IChatClient _chatClient;

    /// <summary>
    /// チェック観点の日本語名マッピング（デフォルト）
    /// </summary>
    private readonly Dictionary<string, string> _perspectiveNames = new()
    {
        { "typo", "誤字・脱字" },
        { "grammar", "文法的誤り" },
        { "contradiction", "意味の矛盾" },
        { "terminology", "用語の不統一" },
        { "ambiguity", "表現の曖昧さ" },
        { "tone", "文章のトーン・文体" },
        { "logic", "論理的整合性" },
        { "readability", "読みやすさ" },
        { "completeness", "情報の完全性" },
        { "accuracy", "事実の正確性" }
    };

    /// <summary>
    /// チェック観点ごとのプロンプト（デフォルト）
    /// </summary>
    private readonly Dictionary<string, string> _perspectivePrompts = new()
    {
        { "typo", "以下の日本語テキストを読み、誤字・脱字がないかチェックしてください。問題がある場合は該当箇所と修正案を示してください。問題がなければ「問題なし」と回答してください。" },
        { "grammar", "以下の日本語テキストを読み、文法的誤り（助詞の誤り、主述の不一致、時制の問題など）がないかチェックしてください。問題がある場合は該当箇所と修正案を示してください。問題がなければ「問題なし」と回答してください。" },
        { "contradiction", "以下の日本語テキストを読み、意味の矛盾や論理的な不整合がないかチェックしてください。問題がある場合は該当箇所と具体的な矛盾点を示してください。問題がなければ「問題なし」と回答してください。" },
        { "terminology", "以下の日本語テキストを読み、用語の表記揺れや不統一がないかチェックしてください。問題がある場合は該当箇所と統一すべき表記を示してください。問題がなければ「問題なし」と回答してください。" },
        { "ambiguity", "以下の日本語テキストを読み、表現が曖昧で読者が誤解する可能性がある箇所がないかチェックしてください。問題がある場合は該当箇所とより明確な表現案を示してください。問題がなければ「問題なし」と回答してください。" },
        { "tone", "以下の日本語テキストを読み、文章のトーンや文体が一貫しているかチェックしてください。問題がある場合は該当箇所と改善案を示してください。問題がなければ「問題なし」と回答してください。" },
        { "logic", "以下の日本語テキストを読み、論理展開が適切で整合性があるかチェックしてください。問題がある場合は該当箇所と改善案を示してください。問題がなければ「問題なし」と回答してください。" },
        { "readability", "以下の日本語テキストを読み、読みやすさに問題がないかチェックしてください。問題がある場合は該当箇所と改善案を示してください。問題がなければ「問題なし」と回答してください。" },
        { "completeness", "以下の日本語テキストを読み、必要な情報が漏れなく記載されているかチェックしてください。問題がある場合は不足している情報を指摘してください。問題がなければ「問題なし」と回答してください。" },
        { "accuracy", "以下の日本語テキストを読み、事実関係に誤りがないかチェックしてください。問題がある場合は該当箇所を指摘してください。問題がなければ「問題なし」と回答してください。" }
    };

    /// <summary>
    /// コンストラクタ
    /// </summary>
    public ValidateChunkExecutor(IChatClient chatClient) : base("ValidateChunkExecutor")
    {
        _chatClient = chatClient;
    }

    /// <summary>
    /// メッセージハンドラーの実装
    /// </summary>
    /// <param name="input">入力の検証状態</param>
    /// <param name="context">ワークフローコンテキスト</param>
    /// <param name="cancellationToken">キャンセレーショントークン</param>
    /// <returns>更新された検証状態</returns>
    public async ValueTask<ValidationState> HandleAsync(
        ValidationState input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            // タスクキューから1件取り出す
            var taskQueue = new Queue<ValidationTask>(input.TaskQueue);
            if (taskQueue.Count == 0)
            {
                // タスクがない場合はそのまま返す
                return input;
            }

            var task = taskQueue.Dequeue();
            var remainingTasks = taskQueue.Count;

            var perspectiveName = _perspectiveNames.GetValueOrDefault(task.Perspective, task.Perspective);
            Console.WriteLine($"[3. チェック実行] チャンク {task.ChunkIndex + 1} - 観点: {perspectiveName} (残り: {remainingTasks})");

            // プロンプトを構築（辞書にない場合は汎用プロンプトを使用）
            string systemPrompt;
            if (_perspectivePrompts.ContainsKey(task.Perspective))
            {
                systemPrompt = _perspectivePrompts[task.Perspective];
            }
            else
            {
                // カスタム観点の場合は、観点名から汎用プロンプトを生成
                systemPrompt = $"以下の日本語テキストを「{task.Perspective}」の観点でチェックしてください。問題がある場合は該当箇所と改善案を示してください。問題がなければ「問題なし」と回答してください。";
            }
            var prompt = $"{systemPrompt}\n\n【テキスト】\n{task.ChunkText}";

            // AIでチェックを実行
            var messages = new List<ChatMessage>
            {
                new(ChatRole.User, prompt)
            };

            var response = await _chatClient.GetResponseAsync(messages, cancellationToken: cancellationToken);
            var findings = response.ToString() ?? string.Empty;

            Console.WriteLine($"[3. チェック完了] チャンク {task.ChunkIndex + 1} - 観点: {perspectiveName}");

            // 結果を蓄積
            var newResults = new List<ValidationResult>(input.Results)
            {
                new ValidationResult
                {
                    ChunkIndex = task.ChunkIndex,
                    Perspective = task.Perspective,
                    Findings = findings,
                    ProcessedAt = DateTime.Now
                }
            };

            // 新しい状態を返す
            var newState = new ValidationState
            {
                OriginalText = input.OriginalText,
                TextChunks = input.TextChunks,
                CheckPerspectives = input.CheckPerspectives,
                TaskQueue = taskQueue,
                Results = newResults,
                ConsolidatedReport = input.ConsolidatedReport,
                Errors = input.Errors
            };

            return newState;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[3. チェック実行] エラー: {ex.Message}");
            var errorState = input;
            errorState.Errors.Add($"チェック処理エラー: {ex.Message}");
            return errorState;
        }
    }
}
