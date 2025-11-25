using Microsoft.AspNetCore.Mvc;
using System.Linq;
using System.Threading.Tasks;
using System;
using System.Collections.Generic;
using MSAgentFramework.RagApp.Models;
using MSAgentFramework.RagApp.Services;

namespace MSAgentFramework.RagApp.Controllers
{
    [ApiController]
    [Route("api/search")]
    public class SearchController : ControllerBase
    {
        private readonly DocumentStoreService _store;

        public SearchController(DocumentStoreService store)
        {
            _store = store;
        }

        [HttpPost]
        public async Task<IActionResult> Search([FromBody] SearchRequestDto req)
        {
            if (req == null || string.IsNullOrEmpty(req.Query)) return BadRequest(new { success = false, error = "query required" });
            var results = await _store.SearchAsync(req.Query, req.NResults, req.Threshold);

            if (!results.Any()) return NotFound(new { success = false, error = "no results" });

            var dtoResults = results.Select((r, idx) => new SearchResultDto
            {
                Rank = idx + 1,
                Filename = r.Doc.Filename,
                Score = Math.Round(r.Score, 4),
                Document = r.Doc.Content,
                CreatedAt = r.Doc.CreatedAt.ToString("o")
            }).ToList();

            return Ok(new
            {
                success = true,
                data = new
                {
                    query = req.Query,
                    threshold = req.Threshold,
                    hit_count = dtoResults.Count,
                    results = dtoResults
                }
            });
        }
    }
}
