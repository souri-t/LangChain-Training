using Microsoft.EntityFrameworkCore;
using MSAgentFramework.RagApp.Models;

namespace MSAgentFramework.RagApp.Data
{
    public class RagContext : DbContext
    {
        public RagContext(DbContextOptions<RagContext> options) : base(options) { }

        public DbSet<Document> Documents { get; set; }
    }
}
