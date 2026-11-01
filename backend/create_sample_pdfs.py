import os
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

def create_simple_pdf(filepath: str, text_lines: list[str]):
    # Minimal valid PDF with a simple content stream
    content = "BT\n/F1 12 Tf\n50 750 Td\n16 TL\n"
    for line in text_lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content += f"({escaped}) '\n"
    content += "ET\n"
    
    stream_bytes = content.encode("latin-1")
    stream_len = len(stream_bytes)

    pdf_text = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {stream_len} >>
stream
{content}endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000000 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
500
%%EOF
"""
    with open(filepath, "wb") as f:
        f.write(pdf_text.encode("latin-1"))

if __name__ == "__main__":
    os.makedirs("./storage/documents", exist_ok=True)
    create_simple_pdf("./storage/documents/test_sample.pdf", [
        "AICTE Verification Document",
        "Institution: Apex Institute of Engineering & Technology",
        "Land Area: 5.0 Acres",
        "Date of Issue: 15/01/2024",
        "Valid up to: 15/01/2029"
    ])
    print("Test PDF written.")
