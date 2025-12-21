namespace TextValidatorAgent.Models;

/// <summary>
/// チャンク×チェック観点の最小処理単位を表すタスク
/// </summary>
public class ValidationTask
{
    /// <summary>
    /// 対象チャンクのインデックス
    /// </summary>
    public int ChunkIndex { get; set; }

    /// <summary>
    /// チャンクのテキスト内容
    /// </summary>
    public string ChunkText { get; set; } = string.Empty;

    /// <summary>
    /// チェック観点（typo, grammar, contradiction, terminology, ambiguity）
    /// </summary>
    public string Perspective { get; set; } = string.Empty;
}
