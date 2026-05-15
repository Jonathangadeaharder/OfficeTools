from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=20)

for p in range(16):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, f"Page {p + 1}: Document Title", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 7, "Sample paragraph content. " * 20)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Section Heading", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 7, "More text under heading. " * 10)
    col_w = 40
    pdf.set_font("Helvetica", "", 10)
    for header in ["Item", "Qty", "Price", "Total"]:
        pdf.cell(col_w, 8, header, border=1)
    pdf.ln()
    for row in range(3):
        for val in [
            f"Item {row + 1}",
            str((p + 1) * (row + 1)),
            f"${row * 2}.50",
            f"${(p + 1) * row}.00",
        ]:
            pdf.cell(col_w, 7, val, border=1)
        pdf.ln()

pdf.output("/tmp/bench_16.pdf")
print(f"Created /tmp/bench_16.pdf ({p + 1} pages)")
