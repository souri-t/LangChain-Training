namespace TextValidatorAgent.Models;

/// <summary>
/// ワークフロー全体で共有される状態
/// </summary>
public class ValidationState
{
    /// <summary>
    /// 入力された元の文章（不変）
    /// </summary>
    public string OriginalText { get; set; } = string.Empty;

    /// <summary>
    /// ユーザーからのチェック依頼文（自然言語）
    /// </summary>
    public string UserCheckRequest { get; set; } = string.Empty;

    /// <summary>
    /// ユーザーが指定したチェック観点の生テキスト（改行区切り、箇条書き、カンマ区切りなど）
    /// 例: "日本語表現的な誤りはないか？\n番号付きリストは連続しているか？"
    /// </summary>
    public string UserCheckPerspectivesText { get; set; } = string.Empty;

    /// <summary>
    /// ユーザーが指定したチェック観点リスト（解析後の配列形式）
    /// ParsePerspectivesTextExecutorで生成される
    /// </summary>
    public List<string> UserCheckPerspectives { get; set; } = new();

    /// <summary>
    /// 分割後の文章チャンクリスト
    /// </summary>
    public List<string> TextChunks { get; set; } = new();

    /// <summary>
    /// チェック観点リスト（typo, grammar, contradiction, terminology, ambiguity）
    /// </summary>
    public List<string> CheckPerspectives { get; set; } = new()
    {
        "typo",          // 誤字・脱字
        "grammar",       // 文法的誤り
        "contradiction", // 意味の矛盾
        "terminology",   // 用語の不統一
        "ambiguity"      // 表現の曖昧さ
    };

    /// <summary>
    /// 未処理タスクのキュー（チャンク×観点の組み合わせ）
    /// </summary>
    public Queue<ValidationTask> TaskQueue { get; set; } = new();

    /// <summary>
    /// チェック結果の蓄積リスト
    /// </summary>
    public List<ValidationResult> Results { get; set; } = new();

    /// <summary>
    /// 統合後の最終レビューレポート
    /// </summary>
    public string ConsolidatedReport { get; set; } = string.Empty;

    /// <summary>
    /// エラーメッセージリスト
    /// </summary>
    public List<string> Errors { get; set; } = new();
}
