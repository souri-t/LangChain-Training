namespace TextValidatorAgent.Models;

/// <summary>
/// 各タスクのチェック結果
/// </summary>
public class ValidationResult
{
    /// <summary>
    /// 対象チャンクのインデックス
    /// </summary>
    public int ChunkIndex { get; set; }

    /// <summary>
    /// チェック観点
    /// </summary>
    public string Perspective { get; set; } = string.Empty;

    /// <summary>
    /// 検出された問題・改善提案
    /// </summary>
    public string Findings { get; set; } = string.Empty;

    /// <summary>
    /// 処理完了日時
    /// </summary>
    public DateTime ProcessedAt { get; set; }
}
