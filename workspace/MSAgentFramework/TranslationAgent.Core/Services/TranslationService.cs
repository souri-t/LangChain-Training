using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using OpenAI;
using TranslationAgent.Core.Executors;
using TranslationAgent.Core.Models;

namespace TranslationAgent.Core.Services;

/// <summary>
/// 翻訳サービスを提供するクラス
/// </summary>
public class TranslationService
{
    private readonly string _apiKey;
    private readonly string _baseUrl;
    private readonly string _modelName;

    public TranslationService(string apiKey, string baseUrl, string modelName)
    {
        _apiKey = apiKey ?? throw new ArgumentNullException(nameof(apiKey));
        _baseUrl = baseUrl ?? throw new ArgumentNullException(nameof(baseUrl));
        _modelName = modelName ?? throw new ArgumentNullException(nameof(modelName));
    }

    /// <summary>
    /// テキストを翻訳します
    /// </summary>
    /// <param name="text">翻訳するテキスト</param>
    /// <param name="onProgress">進捗通知のコールバック（オプション）</param>
    /// <param name="cancellationToken">キャンセルトークン</param>
    /// <returns>翻訳されたテキスト</returns>
    public async Task<string> TranslateAsync(
        string text, 
        Action<string>? onProgress = null,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return string.Empty;
        }

        onProgress?.Invoke("翻訳を開始します...");

        // OpenAI互換のクライアントを作成
        var apiKeyCredential = new System.ClientModel.ApiKeyCredential(_apiKey);
        var openAIClient = new OpenAIClient(apiKeyCredential, new OpenAIClientOptions 
        { 
            Endpoint = new Uri(_baseUrl) 
        });
        var chatClient = openAIClient.GetChatClient(_modelName).AsIChatClient();

        // Executorを作成
        var splitExecutor = new SplitTextExecutor();
        var translateExecutor = new TranslateChunkExecutor(chatClient);
        var combineExecutor = new CombineTranslationsExecutor();

        // ワークフローを構築
        var workflow = new WorkflowBuilder(splitExecutor)
            .AddEdge(splitExecutor, translateExecutor)
            .AddEdge(translateExecutor, translateExecutor, 
                condition: (TranslationState? state) => state != null && state.CurrentIndex < state.TextChunks.Count)
            .AddEdge(translateExecutor, combineExecutor, 
                condition: (TranslationState? state) => state != null && state.CurrentIndex >= state.TextChunks.Count)
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

        onProgress?.Invoke("ワークフローを実行中...");

        // ワークフローを実行
        var run = await InProcessExecution.RunAsync(workflow, initialState);

        // 最終結果を取得
        TranslationState? finalState = null;
        foreach (var evt in run.NewEvents)
        {
            if (evt is ExecutorCompletedEvent completedEvent)
            {
                onProgress?.Invoke($"処理完了: {completedEvent.ExecutorId}");
                
                if (completedEvent.Data is TranslationState state)
                {
                    finalState = state;
                }
            }
            else if (evt is WorkflowOutputEvent outputEvent)
            {
                if (outputEvent.Data is TranslationState state)
                {
                    finalState = state;
                }
            }
        }

        onProgress?.Invoke("翻訳が完了しました。");

        return finalState?.FinalTranslation ?? string.Empty;
    }
}
