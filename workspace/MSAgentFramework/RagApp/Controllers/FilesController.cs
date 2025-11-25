using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System;
using System.Collections.Generic;
using MSAgentFramework.RagApp.Services;
using MSAgentFramework.RagApp.Utils;
using MSAgentFramework.RagApp.Models;

namespace MSAgentFramework.RagApp.Controllers
{
    [ApiController]
    [Route("api/files")]
    public class FilesController : ControllerBase
    {
        private readonly DocumentStoreService _store;

        public FilesController(DocumentStoreService store)
        {
            _store = store;
        }

        [HttpGet("list")]
        public async Task<IActionResult> GetFiles()
        {
            var files = await _store.GetFileListAsync();
            var result = files.Select(f => new FileInfoDto
            {
                DocId = f.Id,
                Filename = f.Filename,
                Directory = f.Directory,
                CreatedAt = f.CreatedAt.ToString("o")
            }).ToList();

            return Ok(new { success = true, data = new { files = result, total_count = result.Count } });
        }

        [HttpPost("upload")]
        public async Task<IActionResult> UploadFiles(List<IFormFile> files)
        {
            if (files == null || files.Count == 0) return BadRequest(new { success = false, error = "No files provided" });

            try
            {
                var texts = new List<string>();
                var filenames = new List<string>();

                foreach (var f in files)
                {
                    filenames.Add(f.FileName);
                    if (f.ContentType == "application/pdf" || f.FileName.EndsWith(".pdf"))
                    {
                        using var stream = f.OpenReadStream();
                        texts.Add(PdfUtils.ExtractText(stream));
                    }
                    else
                    {
                        using var ms = new MemoryStream();
                        await f.CopyToAsync(ms);
                        ms.Position = 0;
                        using var sr = new StreamReader(ms);
                        texts.Add(await sr.ReadToEndAsync());
                    }
                }

                await _store.AddOrReplaceDocumentsAsync(texts, filenames);
                return Ok(new { success = true });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, error = ex.Message });
            }
        }

        [HttpPost("delete")]
        public async Task<IActionResult> DeleteFile([FromBody] string filename)
        {
            if (string.IsNullOrEmpty(filename)) return BadRequest(new { success = false, error = "filename required" });
            await _store.DeleteByFilenameAsync(filename);
            return Ok(new { success = true });
        }

        [HttpPost("update-directories")]
        public async Task<IActionResult> UpdateDirectories([FromBody] List<Dictionary<string, object>> updates)
        {
            var list = new List<(int DocId, string NewDirectory)>();
            foreach (var u in updates)
            {
                if (u.TryGetValue("doc_id", out var docIdObj) && u.TryGetValue("new_directory", out var dirObj))
                {
                    if (int.TryParse(docIdObj.ToString(), out int docId))
                    {
                        list.Add((docId, dirObj.ToString() ?? "/"));
                    }
                }
            }
            await _store.UpdateDirectoriesAsync(list);
            return Ok(new { success = true });
        }
    }
}
