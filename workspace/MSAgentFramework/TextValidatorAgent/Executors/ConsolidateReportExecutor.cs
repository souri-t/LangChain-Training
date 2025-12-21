using Microsoft.Extensions.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TextValidatorAgent.Models;
using System.Text;

namespace TextValidatorAgent.Executors;

/// <summary>
/// 全チェック結果を統合し、最終レビューレポートを生成するExecutor
/// </summary>
public class ConsolidateReportExecutor : ReflectingExecutor<ConsolidateReportExecutor>, IMessageHandler<ValidationState, ValidationState>
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
    /// コンストラクタ
    /// </summary>
    public ConsolidateReportExecutor(IChatClient chatClient) : base("ConsolidateReportExecutor")
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
            Console.WriteLine("[4. レポート統合] 処理開始");
            Console.WriteLine($"   - 総結果数: {input.Results.Count}");

            // 観点別に結果をグループ化して整形
            var reportBuilder = new StringBuilder();
            reportBuilder.AppendLine("=== 文章レビューレポート ===");
            reportBuilder.AppendLine();
            reportBuilder.AppendLine($"チェック実施日時: {DateTime.Now:yyyy年MM月dd日 HH:mm:ss}");
            reportBuilder.AppendLine($"総チャンク数: {input.TextChunks.Count}");
            reportBuilder.AppendLine($"チェック観点数: {input.CheckPerspectives.Count}");
            reportBuilder.AppendLine();

            // 観点ごとにまとめる
            foreach (var perspective in input.CheckPerspectives)
            {
                var perspectiveName = _perspectiveNames.GetValueOrDefault(perspective, perspective);
                reportBuilder.AppendLine($"## 【{perspectiveName}】");
                reportBuilder.AppendLine();

                var perspectiveResults = input.Results
                    .Where(r => r.Perspective == perspective)
                    .OrderBy(r => r.ChunkIndex)
                    .ToList();

                foreach (var result in perspectiveResults)
                {
                    reportBuilder.AppendLine($"### チャンク {result.ChunkIndex + 1}");
                    reportBuilder.AppendLine($"```");
                    reportBuilder.AppendLine(input.TextChunks[result.ChunkIndex]);
                    reportBuilder.AppendLine($"```");
                    reportBuilder.AppendLine($"**チェック結果:** {result.Findings}");
                    reportBuilder.AppendLine();
                }

                reportBuilder.AppendLine();
            }

            // 総評をAIに生成させる（オプション）
            reportBuilder.AppendLine("## 【総合評価】");
            reportBuilder.AppendLine();

            var summaryPrompt = BuildSummaryPrompt(input);
            var messages = new List<ChatMessage>
            {
                new(ChatRole.User, summaryPrompt)
            };

            var response = await _chatClient.GetResponseAsync(messages, cancellationToken: cancellationToken);
            var summary = response.ToString() ?? "総合評価の生成に失敗しました。";
            reportBuilder.AppendLine(summary);

            var finalReport = reportBuilder.ToString();
            Console.WriteLine("[4. レポート統合] 完了");

            // 新しい状態を返す
            var newState = new ValidationState
            {
                OriginalText = input.OriginalText,
                TextChunks = input.TextChunks,
                CheckPerspectives = input.CheckPerspectives,
                TaskQueue = input.TaskQueue,
                Results = input.Results,
                ConsolidatedReport = finalReport,
                Errors = input.Errors
            };

            return newState;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[4. レポート統合] エラー: {ex.Message}");
            var errorState = input;
            errorState.Errors.Add($"レポート統合エラー: {ex.Message}");
            return errorState;
        }
    }

    /// <summary>
    /// 総評生成用のプロンプトを構築
    /// </summary>
    private string BuildSummaryPrompt(ValidationState state)
    {
        var sb = new StringBuilder();
        sb.AppendLine("以下の文章レビュー結果に基づき、簡潔な総合評価（3-5文程度）を作成してください。");
        sb.AppendLine("改善が必要な点と、全体的な文章品質について言及してください。");
        sb.AppendLine();
        sb.AppendLine("【レビュー結果サマリー】");

        foreach (var perspective in state.CheckPerspectives)
        {
            var perspectiveName = _perspectiveNames.GetValueOrDefault(perspective, perspective);
            var issueCount = state.Results
                .Count(r => r.Perspective == perspective && !r.Findings.Contains("問題なし"));
            sb.AppendLine($"- {perspectiveName}: {issueCount}件の指摘");
        }

        return sb.ToString();
    }
}
