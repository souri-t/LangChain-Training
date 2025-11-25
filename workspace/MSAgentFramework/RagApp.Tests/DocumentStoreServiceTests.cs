using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using MSAgentFramework.RagApp.Data;
using MSAgentFramework.RagApp.Models;
using MSAgentFramework.RagApp.Services;
using System.Collections.Generic;
using System.Threading.Tasks;
using Xunit;

namespace MSAgentFramework.RagApp.Tests
{
    class DummyEmbedder : IEmbedder
    {
        public Task<List<List<double>>> EmbedAsync(List<string> texts)
        {
            // Return a simple embedding where each text becomes a vector of its length
            var result = new List<List<double>>();
            foreach (var t in texts) result.Add(new List<double> { t.Length });
            return Task.FromResult(result);
        }
    }

    public class DocumentStoreServiceTests
    {
        [Fact]
        public async Task Search_Returns_Correct_Results()
        {
            var connection = new SqliteConnection("DataSource=:memory:");
            connection.Open();
            var options = new DbContextOptionsBuilder<RagContext>().UseSqlite(connection).Options;
            using (var context = new RagContext(options))
            {
                context.Database.EnsureCreated();
                var embedder = new DummyEmbedder();
                var store = new DocumentStoreService(context, embedder);

                await store.AddOrReplaceDocumentsAsync(new List<string> { "hello world", "this is a test" }, new List<string> { "a.txt", "b.txt" });

                var results = await store.SearchAsync("hello", nResults: 5, threshold: 0.0);
                Assert.NotEmpty(results);
            }
        }
    }
}
