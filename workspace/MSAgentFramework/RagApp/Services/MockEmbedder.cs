using System.Security.Cryptography;
using System.Text;

namespace MSAgentFramework.RagApp.Services;

/// <summary>
/// Mock embedder for testing without external API
/// Generates deterministic embeddings from text hashing
/// </summary>
public class MockEmbedder : IEmbedder
{
    private readonly ILogger<MockEmbedder> _logger;
    private const int EmbeddingDimension = 384; // Standard embedding size

    public MockEmbedder(ILogger<MockEmbedder> logger)
    {
        _logger = logger;
    }

    public async Task<List<List<double>>> EmbedAsync(List<string> texts)
    {
        _logger.LogInformation($"MockEmbedder: Generating embeddings for {texts.Count} texts");
        
        var embeddings = new List<List<double>>();
        foreach (var text in texts)
        {
            embeddings.Add(GenerateMockEmbedding(text).ToList());
        }
        
        // Simulate API delay
        await Task.Delay(100);
        
        return embeddings;
    }

    private double[] GenerateMockEmbedding(string text)
    {
        // Use SHA256 to generate deterministic embedding
        using var sha256 = SHA256.Create();
        var hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(text));
        
        var embedding = new double[EmbeddingDimension];
        
        // Generate embedding from hash
        for (int i = 0; i < EmbeddingDimension; i++)
        {
            // Use multiple hash bytes to generate each dimension
            int byteIndex = (i * hashBytes.Length / EmbeddingDimension) % hashBytes.Length;
            int nextByteIndex = (byteIndex + 1) % hashBytes.Length;
            
            // Combine two bytes to create a value
            int value = (hashBytes[byteIndex] << 8) | hashBytes[nextByteIndex];
            
            // Normalize to [-1, 1] range
            embedding[i] = (value / 65535.0) * 2.0 - 1.0;
        }
        
        // Normalize to unit vector
        double magnitude = Math.Sqrt(embedding.Sum(x => x * x));
        if (magnitude > 0)
        {
            for (int i = 0; i < embedding.Length; i++)
            {
                embedding[i] /= magnitude;
            }
        }
        
        return embedding;
    }
}
