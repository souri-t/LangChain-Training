namespace AgentClient.Models;

/// <summary>
/// チャットメッセージを表すクラス
/// </summary>
public class ChatMessage
{
    public string Role { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; } = DateTime.Now;
}
