namespace MSAgentFramework.RagApp.Models
{
    public class SearchRequestDto
    {
        public string Query { get; set; } = string.Empty;
        public double Threshold { get; set; } = 0.2;
        public int NResults { get; set; } = 5;
    }

    public class FileInfoDto
    {
        public int DocId { get; set; }
        public string Filename { get; set; } = string.Empty;
        public string Directory { get; set; } = string.Empty;
        public string CreatedAt { get; set; } = string.Empty;
    }

    public class SearchResultDto
    {
        public int Rank { get; set; }
        public string Filename { get; set; } = string.Empty;
        public double Score { get; set; }
        public string Document { get; set; } = string.Empty;
        public string? CreatedAt { get; set; }
    }

    public class DirectoryUpdateDto
    {
        public int DocId { get; set; }
        public string NewDirectory { get; set; } = string.Empty;
    }

    public class DirectoryUpdateRequestDto
    {
        public List<DirectoryUpdateDto> Updates { get; set; } = new List<DirectoryUpdateDto>();
    }
}
