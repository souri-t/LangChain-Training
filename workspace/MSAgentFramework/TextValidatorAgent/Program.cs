using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using OpenAI;
using OpenAI.Chat;
using TextValidatorAgent.Configuration;
using TextValidatorAgent.Executors;
using TextValidatorAgent.Models;

namespace TextValidatorAgent;

class Program
{
    static async Task Main(string[] args)
    {
        try
        {
            // 環境変数のチェック
            var apiKey = EnvironmentConfig.GetApiKey();
            var baseUrl = EnvironmentConfig.GetBaseUrl();
            var modelName = EnvironmentConfig.GetModelName();

            Console.WriteLine("=== Microsoft Agent Framework 文章レビューエージェント ===");
            Console.WriteLine($"Model: {modelName}");
            Console.WriteLine($"Base URL: {baseUrl}");
            Console.WriteLine();

            // サンプルテキスト（日本語の長文）
            var sampleText = GetSampleJapaneseText();

            // チェック依頼方法を選択
            // 方法1: 個別の観点を自然文章で指定（推奨）
            var checkPerspectivesText = GetSampleCheckPerspectives();
            
            // 方法2: 自然言語の依頼文（方法1が空の場合に使用）
            var checkRequest = GetSampleCheckRequest();

            Console.WriteLine("=== 入力テキスト ===");
            Console.WriteLine(sampleText);
            Console.WriteLine();
            Console.WriteLine("=== チェック方法 ===");
            if (!string.IsNullOrWhiteSpace(checkPerspectivesText))
            {
                Console.WriteLine("[観点テキスト指定]");
                var previewLines = checkPerspectivesText.Split('\n').Take(5);
                foreach (var line in previewLines)
                {
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        Console.WriteLine($"  {line.Trim()}");
                    }
                }
                if (checkPerspectivesText.Split('\n').Length > 5)
                {
                    Console.WriteLine("  ...");
                }
            }
            else if (!string.IsNullOrWhiteSpace(checkRequest))
            {
                Console.WriteLine($"[依頼文] {checkRequest}");
            }
            else
            {
                Console.WriteLine("[デフォルト観点を使用]");
            }
            Console.WriteLine();
            Console.WriteLine("=== レビュー処理開始 ===");
            Console.WriteLine();

            // レビュー実行
            var result = await ValidateLongText(sampleText, checkPerspectivesText, checkRequest, apiKey, baseUrl, modelName);

            Console.WriteLine();
            Console.WriteLine("=== レビュー結果 ===");
            Console.WriteLine(result);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"エラーが発生しました: {ex.Message}");
            Console.Error.WriteLine(ex.StackTrace);
            Environment.Exit(1);
        }
    }

    /// <summary>
    /// 長文検証のメイン関数
    /// </summary>
    static async Task<string> ValidateLongText(string text, string checkPerspectivesText, string checkRequest, string apiKey, string baseUrl, string modelName)
    {
        // OpenAI互換のクライアントを作成
        var apiKeyCredential = new System.ClientModel.ApiKeyCredential(apiKey);
        var openAIClient = new OpenAIClient(apiKeyCredential, new OpenAIClientOptions 
        { 
            Endpoint = new Uri(baseUrl) 
        });
        var chatClient = openAIClient.GetChatClient(modelName).AsIChatClient();

        // Executorを作成
        var parsePerspectivesTextExecutor = new ParsePerspectivesTextExecutor(chatClient);
        var parseRequestExecutor = new ParseCheckRequestExecutor(chatClient);
        var splitExecutor = new SplitTextExecutor();
        var createTasksExecutor = new CreateValidationTasksExecutor();
        var validateExecutor = new ValidateChunkExecutor(chatClient);
        var consolidateExecutor = new ConsolidateReportExecutor(chatClient);

        // ワークフローを構築
        // ParsePerspectivesText → ParseRequest → Split → CreateTasks → Validate (ループ) → Consolidate
        var workflow = new WorkflowBuilder(parsePerspectivesTextExecutor)   // ワークフロー開始は観点テキスト解析
            .AddEdge(parsePerspectivesTextExecutor, parseRequestExecutor)  // 観点テキスト解析後、チェック依頼解析へ
            .AddEdge(parseRequestExecutor, splitExecutor)                  // チェック依頼解析後、テキスト分割へ
            .AddEdge(splitExecutor, createTasksExecutor)                   // テキスト分割後、タスク作成へ
            .AddEdge(createTasksExecutor, validateExecutor)                // タスク作成後、検証処理へ
            .AddEdge(validateExecutor, validateExecutor, condition: (ValidationState? state) => state != null && state.TaskQueue.Count > 0)  // validateExecutorから自己ループ（条件：タスクキューが空でない）
            .AddEdge(validateExecutor, consolidateExecutor, condition: (ValidationState? state) => state != null && state.TaskQueue.Count == 0) // タスク完了後、統合処理へ
            .WithOutputFrom(consolidateExecutor)
            .Build();

        // 初期状態を作成
        var initialState = new ValidationState
        {
            OriginalText = text,
            UserCheckRequest = checkRequest,
            UserCheckPerspectivesText = checkPerspectivesText,
            UserCheckPerspectives = new List<string>(),  // ParsePerspectivesTextExecutorで設定される
            TextChunks = new List<string>(),
            CheckPerspectives = new List<string>(),  // ParseRequestExecutorで設定される
            TaskQueue = new Queue<ValidationTask>(),
            Results = new List<ValidationResult>(),
            ConsolidatedReport = string.Empty,
            Errors = new List<string>()
        };

        // ワークフローを実行
        var run = await InProcessExecution.RunAsync(workflow, initialState);

        // 最終結果を取得
        ValidationState? finalState = null;
        foreach (var evt in run.NewEvents)
        {
            if (evt is ExecutorCompletedEvent completedEvent)
            {
                Console.WriteLine($"[イベント] {completedEvent.ExecutorId} 完了");
                
                // データを取得（型キャストを試みる）
                if (completedEvent.Data is ValidationState state)
                {
                    finalState = state;
                }
            }
            else if (evt is WorkflowOutputEvent outputEvent)
            {
                Console.WriteLine($"[ワークフロー出力イベント]");
                if (outputEvent.Data is ValidationState state)
                {
                    finalState = state;
                }
            }
        }

        // エラーチェック
        if (finalState != null && finalState.Errors.Count > 0)
        {
            Console.WriteLine();
            Console.WriteLine("=== エラー一覧 ===");
            foreach (var error in finalState.Errors)
            {
                Console.WriteLine($"- {error}");
            }
        }

        return finalState?.ConsolidatedReport ?? string.Empty;
    }

    /// <summary>
    /// サンプル日本語テキストを取得
    /// </summary>
    static string GetSampleJapaneseText()
    {
        var sb = new System.Text.StringBuilder();
        
        sb.AppendLine("人工知能（AI）は、近年著しい発展をとげており、私達の生活の様々な場面で活用されています。例えば、スマートフォンの音声アシスタント、自動運転車、医療診断支援システムなど、多岐にわたる分野で実用化が進んでいます。");
        sb.AppendLine();
        sb.AppendLine("AI技術の中核をなすのは機械学習とディープラーニングです。これらの技術によって、コンピュータは大量のデータから自動的にパターンを学習し、予測や判断を行うことが可能となりました。特にディープラーニングは画像認識、自然言語処理、音声認識などの分野で目覚しい成果をあげています。");
        sb.AppendLine();
        sb.AppendLine("しかし、AI技術の発展には課題も存在します。例えば、アルゴリズムのバイアス問題、プライバシーの保護、雇用への影響などが指摘されてます。また、AI システムの判断根拠が不透明である「ブラックボックス問題」も重要な課題となっています。");
        sb.AppendLine();
        sb.Append("今後、AI技術はさらに進化し、社会にますます深く浸透していくことが予想されます。私たちは、AI技術の恩恵を享受しながらも、その課題に真摯に向き合い、倫理的で持続可能な発展を目指す必要があります。");

        return sb.ToString().Trim();
    }

    /// <summary>
    /// サンプルチェック観点テキストを取得（優先）
    /// </summary>
    static string GetSampleCheckPerspectives()
    {
        // 方法1: 改行区切りで観点を指定（推奨）
        return @"日本語表現的な誤りはないか？
番号付きリストを使う場合に各リストは連続しているか？
文章のトーンは一貫しているか？";

        // 方法2: 箇条書き形式
        // return @"-誤字脱字のチェック
        // - 文法的な誤りの確認
        // - 論理的な整合性";

        // 方法3: カンマ区切り
        // return "トーンの一貫性、専門用語の適切性、読みやすさ";

        // 方法4: 番号付きリスト
        // return @"1. 専門用語は正確に使われているか？
        // 2. 段落の構成は論理的か？
        // 3. 読者にとって分かりやすい表現か？";

        // 個別観点を使わない場合は空文字列を返す
        // return string.Empty;
    }

    /// <summary>
    /// サンプルチェック依頼を取得（方法2: 自然言語）
    /// </summary>
    static string GetSampleCheckRequest()
    {
        // 例1: 特定の観点を指定
        // return "この文章の誤字脱字と文法の誤りをチェックしてください。";

        // 例2: より詳細な依頼
        // return "ビジネス文書として適切かどうか、トーンの一貫性、専門用語の使い方、読みやすさをチェックしてください。";

        // 例3: カスタム観点
        // return "技術文書として、正確性、論理的な構成、専門家にとっての読みやすさを評価してください。";

        // デフォルト観点を使用する場合は空文字列を返す
        return string.Empty;
    }
}
