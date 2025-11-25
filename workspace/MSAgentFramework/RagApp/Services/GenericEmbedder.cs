using Microsoft.Extensions.Configuration;
using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using System.Net.Http.Headers;
using System.Text;
using System.Linq;
using System.Threading.Tasks;

namespace MSAgentFramework.RagApp.Services
{
    public class GenericEmbedder : IEmbedder
    {
        private readonly IConfiguration _configuration;
        private readonly HttpClient _httpClient;
        private readonly string _apiKey;
        private readonly string _embeddingUrl;
        private readonly string _model;

        public GenericEmbedder(IConfiguration configuration, IHttpClientFactory httpClientFactory)
        {
            _configuration = configuration;
            _httpClient = httpClientFactory.CreateClient();
            _apiKey = _configuration.GetValue<string>("Embedder:ApiKey") ?? string.Empty;
            _embeddingUrl = _configuration.GetValue<string>("Embedder:EmbeddingUrl") ?? string.Empty;
            _model = _configuration.GetValue<string>("Embedder:Model") ?? string.Empty;

            if (!string.IsNullOrEmpty(_apiKey))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _apiKey);
            }
        }

        public async Task<List<List<double>>> EmbedAsync(List<string> texts)
        {
            if (string.IsNullOrEmpty(_embeddingUrl) || string.IsNullOrEmpty(_model))
                throw new ArgumentException("EmbeddingUrl and Model must be configured in appsettings.");

            var payload = new
            {
                input = texts,
                model = _model
            };

            var content = new StringContent(Newtonsoft.Json.JsonConvert.SerializeObject(payload), Encoding.UTF8, "application/json");
            var res = await _httpClient.PostAsync(_embeddingUrl, content);
            res.EnsureSuccessStatusCode();
            var json = await res.Content.ReadAsStringAsync();
            var obj = JObject.Parse(json);
            // Expect OpenAI-like 'data' array
            var arr = obj["data"]?.Select(t => t["embedding"].Select(e => (double)e).ToList()).ToList();
            return arr ?? new List<List<double>>();
        }
    }
}
