using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using OpenAI;
using OpenAI.Chat;
using TranslationAgent.Configuration;
using TranslationAgent.Executors;
using TranslationAgent.Models;

namespace TranslationAgent;

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

            Console.WriteLine("=== Microsoft Agent Framework 翻訳エージェント ===");
            Console.WriteLine($"Model: {modelName}");
            Console.WriteLine($"Base URL: {baseUrl}");
            Console.WriteLine();

            // サンプルテキスト
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of \"intelligent agents\": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.");
            sb.AppendLine();
            sb.AppendLine("Colloquially, the term \"artificial intelligence\" is often used to describe machines (or computers) that mimic \"cognitive\" functions that humans associate with the human mind, such as \"learning\" and \"problem solving\". As machines become increasingly capable, tasks considered to require \"intelligence\" are often removed from the definition of AI, a phenomenon known as the AI effect.");
            sb.AppendLine();
            sb.Append("A machine with artificial general intelligence should be able to solve a wide variety of problems with breadth and versatility similar to human intelligence.");
            var sampleText = sb.ToString().Trim();

            // 翻訳実行
            var result = await TranslateLongText(sampleText, apiKey, baseUrl, modelName);

            Console.WriteLine();
            Console.WriteLine("=== 翻訳結果 ===");
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
    /// 長文翻訳のメイン関数
    /// </summary>
    static async Task<string> TranslateLongText(string text, string apiKey, string baseUrl, string modelName)
    {
        // OpenAI互換のクライアントを作成
        var apiKeyCredential = new System.ClientModel.ApiKeyCredential(apiKey);
        var openAIClient = new OpenAIClient(apiKeyCredential, new OpenAIClientOptions 
        { 
            Endpoint = new Uri(baseUrl) 
        });
        var chatClient = openAIClient.GetChatClient(modelName).AsIChatClient();

        // Executorを作成
        var splitExecutor = new SplitTextExecutor();
        var translateExecutor = new TranslateChunkExecutor(chatClient);
        var combineExecutor = new CombineTranslationsExecutor();

        // ワークフローを構築
        // Microsoft Agent Frameworkでは、LangGraphのような動的なループではなく、
        // 条件付きエッジで分岐を制御します
        var workflow = new WorkflowBuilder(splitExecutor)
            .AddEdge(splitExecutor, translateExecutor)
            // translateExecutorから次の処理へ条件分岐（条件：現在のインデックスがテキストチャンクの数未満）
            .AddEdge(translateExecutor, translateExecutor, condition: (TranslationState? state) => state != null && state.CurrentIndex < state.TextChunks.Count)
            .AddEdge(translateExecutor, combineExecutor, condition: (TranslationState? state) => state != null && state.CurrentIndex >= state.TextChunks.Count)
            .WithOutputFrom(combineExecutor)
            .Build();

        // 初期状態を作成
        var initialState = new TranslationState
        {
            OriginalText = text,
            TextChunks = new List<string>(),
            TranslatedChunks = new List<string>(),
            CurrentIndex = 0,
            FinalTranslation = string.Empty
        };

        // ワークフローを実行
        var run = await InProcessExecution.RunAsync(workflow, initialState);

        // 最終結果を取得
        TranslationState? finalState = null;
        foreach (var evt in run.NewEvents)
        {
            if (evt is ExecutorCompletedEvent completedEvent)
            {
                Console.WriteLine($"[イベント] {completedEvent.ExecutorId} 完了");
                
                // データを取得（型キャストを試みる）
                if (completedEvent.Data is TranslationState state)
                {
                    finalState = state;
                }
            }
            else if (evt is WorkflowOutputEvent outputEvent)
            {
                Console.WriteLine($"[ワークフロー出力] {outputEvent}");
                if (outputEvent.Data is TranslationState state)
                {
                    finalState = state;
                }
            }
        }

        return finalState?.FinalTranslation ?? string.Empty;
    }
}
