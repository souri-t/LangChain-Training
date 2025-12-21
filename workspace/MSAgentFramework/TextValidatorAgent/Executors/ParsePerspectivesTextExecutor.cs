using Microsoft.Extensions.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using TextValidatorAgent.Models;
using System.Text.Json;

namespace TextValidatorAgent.Executors;

/// <summary>
/// ユーザーからの自然文章形式のチェック観点を解析し、個別の観点リストに分解するExecutor
/// </summary>
public class ParsePerspectivesTextExecutor : ReflectingExecutor<ParsePerspectivesTextExecutor>, IMessageHandler<ValidationState, ValidationState>
{
    /// <summary>
    /// チャットクライアント
    /// </summary>
    private readonly IChatClient _chatClient;

    /// <summary>
    /// コンストラクタ
    /// </summary>
    public ParsePerspectivesTextExecutor(IChatClient chatClient) : base("ParsePerspectivesTextExecutor")
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
            Console.WriteLine("[0A. 観点テキスト解析] 処理開始");

            // UserCheckPerspectivesTextが空の場合はスキップ
            if (string.IsNullOrWhiteSpace(input.UserCheckPerspectivesText))
            {
                Console.WriteLine("[0A. 観点テキスト解析] 観点テキストが空のため、スキップ");
                return input;
            }

            Console.WriteLine($"[0A. 観点テキスト解析] 入力テキスト:");
            Console.WriteLine(input.UserCheckPerspectivesText);
            Console.WriteLine();

            // LLMで観点テキストを解析してリスト化
            var prompt = BuildParsePrompt(input.UserCheckPerspectivesText);
            var messages = new List<ChatMessage>
            {
                new(ChatRole.User, prompt)
            };

            var response = await _chatClient.GetResponseAsync(messages, cancellationToken: cancellationToken);
            var responseText = response.ToString() ?? string.Empty;

            Console.WriteLine($"[0A. 観点テキスト解析] LLM応答:");
            Console.WriteLine(responseText);
            Console.WriteLine();

            // JSON形式で観点リストを抽出
            var perspectives = ParsePerspectives(responseText);

            if (perspectives.Count == 0)
            {
                Console.WriteLine("[0A. 観点テキスト解析] 警告: 観点の抽出に失敗、元のテキストを1つの観点として使用");
                perspectives = new List<string> { input.UserCheckPerspectivesText };
            }

            Console.WriteLine($"[0A. 観点テキスト解析] 完了 - {perspectives.Count}個の観点を抽出");
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
                UserCheckPerspectives = perspectives,  // 解析結果を設定
                TextChunks = input.TextChunks,
                CheckPerspectives = input.CheckPerspectives,
                TaskQueue = input.TaskQueue,
                Results = input.Results,
                ConsolidatedReport = input.ConsolidatedReport,
                Errors = input.Errors
            };

            return newState;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[0A. 観点テキスト解析] エラー: {ex.Message}");
            var errorState = input;
            errorState.Errors.Add($"観点テキスト解析エラー: {ex.Message}");
            // エラー時は元のテキストを1つの観点として使用
            if (!string.IsNullOrWhiteSpace(input.UserCheckPerspectivesText))
            {
                errorState.UserCheckPerspectives = new List<string> { input.UserCheckPerspectivesText };
            }
            return errorState;
        }
    }

    /// <summary>
    /// 観点テキスト解析用のプロンプトを構築
    /// </summary>
    private string BuildParsePrompt(string perspectivesText)
    {
        var prompt = @"あなたは文章レビューシステムのチェック観点分解担当です。
ユーザーから以下のような形式で与えられたチェック観点のテキストを、個別の観点に分解してください。

【入力テキスト】
" + perspectivesText + @"

【タスク】
上記のテキストから、個別のチェック観点を抽出し、JSON配列形式で出力してください。

【出力形式】
JSON配列形式で、各観点を文字列として出力してください。

例1（改行区切りの場合）:
入力:
日本語表現的な誤りはないか？
番号付きリストを使う場合に各リストは連続しているか？
文章のトーンは一貫しているか？

出力:
[
  ""日本語表現的な誤りはないか？"",
  ""番号付きリストを使う場合に各リストは連続しているか？"",
  ""文章のトーンは一貫しているか？""
]

例2（箇条書きの場合）:
入力:
- 誤字脱字のチェック
- 文法的な誤りの確認
- 論理的な整合性

出力:
[
  ""誤字脱字のチェック"",
  ""文法的な誤りの確認"",
  ""論理的な整合性""
]

例3（カンマ区切りの場合）:
入力:
トーンの一貫性、専門用語の適切性、読みやすさ

出力:
[
  ""トーンの一貫性"",
  ""専門用語の適切性"",
  ""読みやすさ""
]

【注意事項】
- 各観点は疑問形でも平叙文でも構いません
- 観点は元の表現をできるだけ保持してください
- 改行、箇条書き記号（-、*、•）、番号（1.、2.、など）、カンマなどで区切られた項目を個別の観点として抽出してください
- JSON形式のみを出力してください。説明文は不要です。";

        return prompt;
    }

    /// <summary>
    /// LLM応答から観点リストを抽出
    /// </summary>
    private List<string> ParsePerspectives(string responseText)
    {
        var perspectives = new List<string>();

        try
        {
            // JSON部分を抽出
            var jsonText = ExtractJsonFromResponse(responseText);

            // JSONをパース
            var jsonArray = JsonSerializer.Deserialize<string[]>(jsonText);
            if (jsonArray != null)
            {
                foreach (var item in jsonArray)
                {
                    if (!string.IsNullOrWhiteSpace(item))
                    {
                        perspectives.Add(item.Trim());
                    }
                }
            }
        }
        catch (JsonException ex)
        {
            Console.Error.WriteLine($"JSON解析エラー: {ex.Message}");
            Console.Error.WriteLine($"応答テキスト: {responseText}");
            
            // フォールバック: 改行で分割を試みる
            perspectives = FallbackParsing(responseText);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"観点抽出エラー: {ex.Message}");
            perspectives = FallbackParsing(responseText);
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

    /// <summary>
    /// フォールバック: JSON解析に失敗した場合の簡易パース
    /// </summary>
    private List<string> FallbackParsing(string text)
    {
        Console.WriteLine("[0A. 観点テキスト解析] フォールバック処理: 改行・記号で分割を試行");
        
        var perspectives = new List<string>();
        var lines = text.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);

        foreach (var line in lines)
        {
            var cleaned = line.Trim();
            
            // JSON配列の記号を除去
            cleaned = cleaned.Trim('[', ']', ',', '"', ' ');
            
            // 箇条書き記号を除去
            cleaned = System.Text.RegularExpressions.Regex.Replace(cleaned, @"^[-*•]\s*", "");
            
            // 番号を除去
            cleaned = System.Text.RegularExpressions.Regex.Replace(cleaned, @"^\d+\.\s*", "");
            
            if (!string.IsNullOrWhiteSpace(cleaned))
            {
                perspectives.Add(cleaned);
            }
        }

        return perspectives;
    }
}
