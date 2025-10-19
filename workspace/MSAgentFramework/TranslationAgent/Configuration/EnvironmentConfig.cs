using Microsoft.Extensions.Configuration;

namespace TranslationAgent.Configuration;

/// <summary>
/// 環境変数を読み込むヘルパークラス
/// </summary>
public static class EnvironmentConfig
{
    private static IConfiguration? _configuration;

    public static IConfiguration Configuration
    {
        get
        {
            if (_configuration == null)
            {
                LoadConfiguration();
            }
            return _configuration!;
        }
    }

    private static void LoadConfiguration()
    {
        var builder = new ConfigurationBuilder()
            .AddEnvironmentVariables();

        // .envファイルがあれば読み込む（手動パース）
        var envFilePath = Path.Combine(Directory.GetCurrentDirectory(), ".env");
        if (File.Exists(envFilePath))
        {
            foreach (var line in File.ReadAllLines(envFilePath))
            {
                // コメント行と空行をスキップ
                if (string.IsNullOrWhiteSpace(line) || line.TrimStart().StartsWith("#"))
                    continue;

                var parts = line.Split('=', 2, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length == 2)
                {
                    var key = parts[0].Trim();
                    var value = parts[1].Trim();
                    Environment.SetEnvironmentVariable(key, value);
                }
            }
        }

        _configuration = builder.Build();
    }

    public static string GetApiKey() => 
        Configuration["API_KEY"] ?? throw new InvalidOperationException("API_KEY環境変数が設定されていません。");

    public static string GetBaseUrl() => 
        Configuration["BASE_URL"] ?? throw new InvalidOperationException("BASE_URL環境変数が設定されていません。");

    public static string GetModelName() => 
        Configuration["MODEL_NAME"] ?? "gpt-4o-mini";
}
