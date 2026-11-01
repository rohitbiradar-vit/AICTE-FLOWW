import os
import hashlib
from pypdf import PdfWriter

def make_clean_pdf(output_path: str, lines: list[str]):
    # Form a compliant PDF stream
    text_ops = ["BT", "/F1 12 Tf", "50 720 Td", "18 TL"]
    for l in lines:
        escaped = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_ops.append(f"({escaped}) '")
    text_ops.append("ET")
    stream = "\n".join(text_ops) + "\n"
    stream_bytes = stream.encode("latin-1")
    length = len(stream_bytes)

    objects = []
    # 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # 3: Page
    objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
    # 4: Stream
    objects.append(f"4 0 obj\n<< /Length {length} >>\nstream\n{stream}endstream\nendobj\n")
    # 5: Font
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    header = "%PDF-1.4\n"
    offsets = []
    pos = len(header.encode("latin-1"))
    body = ""
    for obj in objects:
        offsets.append(pos)
        body += obj
        pos += len(obj.encode("latin-1"))

    xref_pos = pos
    xref = "xref\n0 6\n0000000000 65535 f \n"
    for o in offsets:
        xref += f"{o:010d} 00000 n \n"
    
    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"

    full_pdf = (header + body + xref + trailer).encode("latin-1")
    with open(output_path, "wb") as f:
        f.write(full_pdf)

if __name__ == "__main__":
    os.makedirs("./storage/documents", exist_ok=True)
    make_clean_pdf("./storage/documents/clean_test.pdf", [
        "Government of India - AICTE Scrutiny Document",
        "Institution: Apex Institute of Engineering & Technology",
        "Land Area: 5.0 Acres",
        "Built-up Area: 8500 Sq.Meters",
        "Date of Issue: 12/03/2024",
        "Valid up to: 12/03/2029"
    ])
