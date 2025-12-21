using Microsoft.Extensions.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TextValidatorAgent.Models;
using System.Text.Json;

namespace TextValidatorAgent.Executors;

/// <summary>
/// ユーザーからのチェック依頼文を解析し、具体的なチェック観点に分解するExecutor
/// </summary>
public class ParseCheckRequestExecutor : ReflectingExecutor<ParseCheckRequestExecutor>, IMessageHandler<ValidationState, ValidationState>
{
    /// <summary>
    /// チャットクライアント
    /// </summary>
    private readonly IChatClient _chatClient;

    /// <summary>
    /// コンストラクタ
    /// </summary>
    public ParseCheckRequestExecutor(IChatClient chatClient) : base("ParseCheckRequestExecutor")
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
            Console.WriteLine("[0. チェック依頼解析] 処理開始");

            // ユーザー指定の観点リストが存在する場合はそれを優先
            if (input.UserCheckPerspectives != null && input.UserCheckPerspectives.Count > 0)
            {
                Console.WriteLine($"[0. チェック依頼解析] ユーザー指定の観点を使用 ({input.UserCheckPerspectives.Count}個)");
                foreach (var perspective in input.UserCheckPerspectives)
                {
                    Console.WriteLine($"   - {perspective}");
                }

                var userPerspectiveState = new ValidationState
                {
                    OriginalText = input.OriginalText,
                    UserCheckRequest = input.UserCheckRequest,
                    UserCheckPerspectivesText = input.UserCheckPerspectivesText,
                    UserCheckPerspectives = input.UserCheckPerspectives,
                    TextChunks = input.TextChunks,
                    CheckPerspectives = input.UserCheckPerspectives, // そのまま使用
                    TaskQueue = input.TaskQueue,
                    Results = input.Results,
                    ConsolidatedReport = input.ConsolidatedReport,
                    Errors = input.Errors
                };
                return userPerspectiveState;
            }

            Console.WriteLine($"   依頼内容: {input.UserCheckRequest}");

            // チェック依頼が空の場合はデフォルトの観点を使用
            if (string.IsNullOrWhiteSpace(input.UserCheckRequest))
            {
                Console.WriteLine("[0. チェック依頼解析] 依頼が空のため、デフォルトの観点を使用");
                var defaultState = new ValidationState
                {
                    OriginalText = input.OriginalText,
                    UserCheckRequest = input.UserCheckRequest,
                    UserCheckPerspectivesText = input.UserCheckPerspectivesText,
                    UserCheckPerspectives = input.UserCheckPerspectives ?? new List<string>(),
                    TextChunks = input.TextChunks,
                    CheckPerspectives = new List<string>
                    {
                        "typo",          // 誤字・脱字
                        "grammar",       // 文法的誤り
                        "contradiction", // 意味の矛盾
                        "terminology",   // 用語の不統一
                        "ambiguity"      // 表現の曖昧さ
                    },
                    TaskQueue = input.TaskQueue,
                    Results = input.Results,
                    ConsolidatedReport = input.ConsolidatedReport,
                    Errors = input.Errors
                };
                return defaultState;
            }

            // LLMでチェック依頼を解析
            var prompt = BuildParsePrompt(input.UserCheckRequest);
            var messages = new List<ChatMessage>
            {
                new(ChatRole.User, prompt)
            };

            var response = await _chatClient.GetResponseAsync(messages, cancellationToken: cancellationToken);
            var responseText = response.ToString() ?? string.Empty;

            Console.WriteLine($"[0. チェック依頼解析] LLM応答: {responseText}");

            // JSON形式でチェック観点リストを抽出
            var perspectives = ParsePerspectives(responseText);

            if (perspectives.Count == 0)
            {
                Console.WriteLine("[0. チェック依頼解析] 観点の抽出に失敗、デフォルトを使用");
                perspectives = new List<string> { "typo", "grammar", "contradiction", "terminology", "ambiguity" };
            }

            Console.WriteLine($"[0. チェック依頼解析] 完了 - {perspectives.Count}個の観点を抽出");
            foreach (var perspective in perspectives)
            {
                Console.WriteLine($"   - {perspective}");
            }

            // 新しい状態を返す
            var newState = new ValidationState
            {
                OriginalText = input.OriginalText,
                UserCheckRequest = input.UserCheckRequest,
                UserCheckPerspectivesText = input.UserCheckPerspectivesText,
                UserCheckPerspectives = input.UserCheckPerspectives ?? new List<string>(),
                TextChunks = input.TextChunks,
                CheckPerspectives = perspectives,
                TaskQueue = input.TaskQueue,
                Results = input.Results,
                ConsolidatedReport = input.ConsolidatedReport,
                Errors = input.Errors
            };

            return newState;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[0. チェック依頼解析] エラー: {ex.Message}");
            var errorState = input;
            errorState.Errors.Add($"チェック依頼解析エラー: {ex.Message}");
            // エラー時はデフォルトの観点を使用
            errorState.CheckPerspectives = new List<string> { "typo", "grammar", "contradiction", "terminology", "ambiguity" };
            return errorState;
        }
    }

    /// <summary>
    /// チェック依頼解析用のプロンプトを構築
    /// </summary>
    private string BuildParsePrompt(string userRequest)
    {
        var prompt = @"あなたは文章レビューシステムのタスク分解担当です。
ユーザーからの以下のチェック依頼を分析し、具体的なチェック観点に分解してください。

【ユーザーの依頼】
" + userRequest + @"

【出力形式】
JSON配列形式で、各チェック観点を""key""（英数字のID）と""description""（日本語の説明）のペアで出力してください。

例：
[
  {""key"": ""typo"", ""description"": ""誤字・脱字のチェック""},
  {""key"": ""grammar"", ""description"": ""文法的誤りのチェック""},
  {""key"": ""tone"", ""description"": ""文章のトーンの一貫性チェック""}
]

【利用可能な標準観点】
- typo: 誤字・脱字
- grammar: 文法的誤り
- contradiction: 意味の矛盾
- terminology: 用語の不統一
- ambiguity: 表現の曖昧さ
- tone: 文章のトーン・文体
- logic: 論理的整合性
- readability: 読みやすさ
- completeness: 情報の完全性
- accuracy: 事実の正確性

依頼内容に応じて、標準観点を選択するか、必要に応じて新しい観点を定義してください。
JSON形式のみを出力してください。説明文は不要です。";

        return prompt;
    }

    /// <summary>
    /// LLM応答からチェック観点リストを抽出
    /// </summary>
    private List<string> ParsePerspectives(string responseText)
    {
        var perspectives = new List<string>();

        try
        {
            // JSON部分を抽出（```json ``` で囲まれている場合を考慮）
            var jsonText = ExtractJsonFromResponse(responseText);

            // JSONをパース
            var jsonArray = JsonSerializer.Deserialize<JsonElement[]>(jsonText);
            if (jsonArray != null)
            {
                foreach (var item in jsonArray)
                {
                    if (item.TryGetProperty("key", out var keyElement))
                    {
                        var key = keyElement.GetString();
                        if (!string.IsNullOrWhiteSpace(key))
                        {
                            perspectives.Add(key);
                        }
                    }
                }
            }
        }
        catch (JsonException ex)
        {
            Console.Error.WriteLine($"JSON解析エラー: {ex.Message}");
            Console.Error.WriteLine($"応答テキスト: {responseText}");
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"観点抽出エラー: {ex.Message}");
        }

        return perspectives;
    }

    /// <summary>
    /// レスポンステキストからJSON部分を抽出
    /// </summary>
    private string ExtractJsonFromResponse(string responseText)
    {
        // ```json ``` で囲まれている場合
        var jsonMatch = System.Text.RegularExpressions.Regex.Match(responseText, @"```json\s*(\[.*?\])\s*```", System.Text.RegularExpressions.RegexOptions.Singleline);
        if (jsonMatch.Success)
        {
            return jsonMatch.Groups[1].Value.Trim();
        }

        // ``` ``` で囲まれている場合
        jsonMatch = System.Text.RegularExpressions.Regex.Match(responseText, @"```\s*(\[.*?\])\s*```", System.Text.RegularExpressions.RegexOptions.Singleline);
        if (jsonMatch.Success)
        {
            return jsonMatch.Groups[1].Value.Trim();
        }

        // [ ] で始まる部分を抽出
        jsonMatch = System.Text.RegularExpressions.Regex.Match(responseText, @"(\[.*?\])", System.Text.RegularExpressions.RegexOptions.Singleline);
        if (jsonMatch.Success)
        {
            return jsonMatch.Groups[1].Value.Trim();
        }

        // そのまま返す
        return responseText.Trim();
    }
}
