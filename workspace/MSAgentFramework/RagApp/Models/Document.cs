using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace MSAgentFramework.RagApp.Models
{
    public class Document
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string Filename { get; set; } = string.Empty;
        public string Directory { get; set; } = "/";
        public string Content { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        // Embedding stored as JSON array
        public string? EmbeddingJson { get; set; }
    }
}
