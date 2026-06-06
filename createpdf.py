from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

lines = [
    "Our clinic is open from 9 AM to 6 PM.",
    "We are closed on Sundays.",
    "Doctor consultation fee is 500 rupees.",
    "We accept cash and UPI payments.",
    "Emergency contact: 98765-43210.",
]

for line in lines:
    pdf.cell(200, 10, txt=line, ln=True)

pdf.output("document.pdf")
print("PDF created!")
