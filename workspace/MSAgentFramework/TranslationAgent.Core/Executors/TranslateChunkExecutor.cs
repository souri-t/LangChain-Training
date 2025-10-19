using Microsoft.Extensions.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;
using OpenAI;
using TranslationAgent.Core.Models;

namespace TranslationAgent.Core.Executors;

/// <summary>
/// 現在のチャンクを翻訳するExecutor
/// </summary>
public class TranslateChunkExecutor : ReflectingExecutor<TranslateChunkExecutor>, IMessageHandler<TranslationState, TranslationState>
{
    /// <summary>
    /// チャットクライアント
    /// </summary>
    private readonly IChatClient _chatClient;

    /// <summary>
    /// コンストラクタ
    /// </summary>
    public TranslateChunkExecutor(IChatClient chatClient) : base("TranslateChunkExecutor")
    {
        _chatClient = chatClient;
    }

    /// <summary>
    /// メッセージハンドラーの実装
    /// </summary>
    /// <param name="input">入力の翻訳状態</param>
    /// <param name="context">ワークフローコンテキスト</param>
    /// <param name="cancellationToken">キャンセレーショントークン</param>
    /// <returns>更新された翻訳状態</returns>
    public async ValueTask<TranslationState> HandleAsync(
        TranslationState input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        // 現在のチャンクインデックスと総チャンク数を取得
        var currentIdx = input.CurrentIndex;
        var totalChunks = input.TextChunks.Count;
        
        Console.WriteLine($"[2. ノード実行(translate)] チャンク翻訳 ({currentIdx + 1}/{totalChunks})");

        // 現在のチャンクを取得
        var chunk = input.TextChunks[currentIdx];

        // 翻訳プロンプトを作成
        var prompt = $"以下の英文を自然な日本語に翻訳してください。翻訳文のみを出力してください：\n\n{chunk}";

        // AIで翻訳を実行
        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, prompt)
        };

        var response = await _chatClient.GetResponseAsync(messages, cancellationToken: cancellationToken);
        var translatedText = response.ToString() ?? string.Empty;

        // 翻訳結果を状態に保存
        var newTranslatedChunks = new List<string>(input.TranslatedChunks);
        newTranslatedChunks[currentIdx] = translatedText;

        Console.WriteLine($"[2. ノード完了(translate)] チャンク {currentIdx + 1} の翻訳完了");

        // 新しい状態を返す
        var newState = new TranslationState
        {
            OriginalText = input.OriginalText,
            TextChunks = input.TextChunks,
            TranslatedChunks = newTranslatedChunks,
            CurrentIndex = currentIdx + 1,
            FinalTranslation = input.FinalTranslation
        };

        return newState;
    }
}
