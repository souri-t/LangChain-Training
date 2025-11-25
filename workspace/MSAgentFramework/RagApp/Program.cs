using Microsoft.EntityFrameworkCore;
using MSAgentFramework.RagApp.Data;
using MSAgentFramework.RagApp.Services;

var builder = WebApplication.CreateBuilder(args);

// Configuration
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add DbContext (SQLite)
var connectionString = builder.Configuration.GetConnectionString("RagDb") ?? "Data Source=ragapp.db";
builder.Services.AddDbContext<RagContext>(opt => opt.UseSqlite(connectionString));

// DI for services
builder.Services.AddHttpClient();
// Use MockEmbedder for testing without external API
builder.Services.AddScoped<IEmbedder, MockEmbedder>();
// For production with real API, use:
// builder.Services.AddScoped<IEmbedder, GenericEmbedder>();
builder.Services.AddScoped<DocumentStoreService, DocumentStoreService>();

var app = builder.Build();

// Ensure DB created
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<RagContext>();
    db.Database.EnsureCreated();
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseDefaultFiles();
app.UseStaticFiles();

app.UseRouting();
app.UseAuthorization();
app.MapControllers();

app.Run();
