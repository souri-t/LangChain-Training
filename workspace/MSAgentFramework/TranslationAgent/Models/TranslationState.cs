namespace TranslationAgent.Models;

/// <summary>
/// 翻訳ワークフローの状態を表すクラス
/// </summary>
public class TranslationState
{
    /// <summary>
    /// 元の入力テキスト
    /// </summary>
    public string OriginalText { get; set; } = string.Empty;

    /// <summary>
    /// 分割されたテキストチャンク
    /// </summary>
    public List<string> TextChunks { get; set; } = new();

    /// <summary>
    /// 翻訳されたチャンク
    /// </summary>
    public List<string> TranslatedChunks { get; set; } = new();

    /// <summary>
    /// 現在処理中のチャンクのインデックス
    /// </summary>
    public int CurrentIndex { get; set; } = 0;

    /// <summary>
    /// 最終的な翻訳結果
    /// </summary>
    public string FinalTranslation { get; set; } = string.Empty;
}
