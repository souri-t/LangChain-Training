using UglyToad.PdfPig;
using System.Text;

namespace MSAgentFramework.RagApp.Utils
{
    public static class PdfUtils
    {
        public static string ExtractText(Stream stream)
        {
            using var reader = PdfDocument.Open(stream);
            var sb = new StringBuilder();
            foreach (var page in reader.GetPages())
            {
                sb.AppendLine(page.Text);
            }
            return sb.ToString();
        }
    }
}
