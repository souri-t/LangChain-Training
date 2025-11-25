using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using MSAgentFramework.RagApp.Data;
using MSAgentFramework.RagApp.Models;
using Newtonsoft.Json;
using System.Numerics;
using System.Linq;
using System.Threading.Tasks;

namespace MSAgentFramework.RagApp.Services
{
    public class DocumentStoreService
    {
        private readonly RagContext _context;
        private readonly IEmbedder _embedder;

        public DocumentStoreService(RagContext context, IEmbedder embedder)
        {
            _context = context;
            _embedder = embedder;
        }

        public async Task AddOrReplaceDocumentsAsync(List<string> texts, List<string> filenames)
        {
            var embeddings = await _embedder.EmbedAsync(texts);
            for (int i = 0; i < filenames.Count; i++)
            {
                var filename = filenames[i];
                var text = texts[i];
                await DeleteByFilenameAsync(filename);
                var doc = new Document
                {
                    Filename = filename,
                    Content = text,
                    EmbeddingJson = JsonConvert.SerializeObject(embeddings[i]),
                    CreatedAt = DateTime.UtcNow
                };
                _context.Documents.Add(doc);
            }
            await _context.SaveChangesAsync();
        }

        public async Task<List<Document>> GetFileListAsync()
        {
            return await _context.Documents.AsNoTracking().OrderBy(d => d.CreatedAt).ToListAsync();
        }

        public async Task DeleteByFilenameAsync(string filename)
        {
            var list = await _context.Documents.Where(d => d.Filename == filename).ToListAsync();
            if (list.Any())
            {
                _context.Documents.RemoveRange(list);
                await _context.SaveChangesAsync();
            }
        }

        public async Task UpdateDirectoriesAsync(List<(int DocId, string NewDirectory)> updates)
        {
            foreach (var u in updates)
            {
                var d = await _context.Documents.FindAsync(u.DocId);
                if (d != null)
                {
                    d.Directory = u.NewDirectory;
                }
            }
            await _context.SaveChangesAsync();
        }

        private static double L2Distance(List<double> a, List<double> b)
        {
            if (a == null || b == null) return double.MaxValue;
            var min = Math.Min(a.Count, b.Count);
            double sum = 0;
            for (int i = 0; i < min; i++) sum += (a[i] - b[i]) * (a[i] - b[i]);
            return Math.Sqrt(sum);
        }

        public async Task<List<(Document Doc, double Score)>> SearchAsync(string query, int nResults = 5, double threshold = 0.7)
        {
            // embed query
            var qEmbed = (await _embedder.EmbedAsync(new List<string> { query })).FirstOrDefault();
            if (qEmbed == null) return new List<(Document, double)>();

            var docs = await _context.Documents.AsNoTracking().ToListAsync();
            var results = new List<(Document Doc, double Score)>();
            foreach (var doc in docs)
            {
                if (string.IsNullOrEmpty(doc.EmbeddingJson)) continue;
                var emb = JsonConvert.DeserializeObject<List<double>>(doc.EmbeddingJson) ?? new List<double>();
                var dist = L2Distance(qEmbed, emb);
                var similarity = 1.0 / (1.0 + dist);
                if (similarity >= threshold)
                    results.Add((doc, similarity));
            }

            return results.OrderByDescending(r => r.Score).Take(nResults).ToList();
        }
    }
}
