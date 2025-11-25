using System.Collections.Generic;
namespace MSAgentFramework.RagApp.Services
{
    public interface IEmbedder
    {
        Task<List<List<double>>> EmbedAsync(List<string> texts);
    }
}
