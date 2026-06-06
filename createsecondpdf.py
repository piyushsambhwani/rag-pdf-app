from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

lines = [
    "We offer three packages: Basic, Standard, and Premium.",
    "Basic package costs 999 rupees per month.",
    "Standard package costs 1999 rupees per month.",
    "Premium package costs 3999 rupees per month.",
    "All packages include free home delivery.",
    "Contact our sales team at sales@company.com.",
    "We offer 30 day free trial for all packages.",
    "Discounts available for annual subscriptions.",
]

for line in lines:
    pdf.cell(200, 10, txt=line, ln=True)

pdf.output("documents/packages.pdf")
print("Second PDF created!")
