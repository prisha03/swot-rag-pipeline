# utils.py

from fpdf import FPDF
from extract_text import clean_text  # Adjust path if needed
import re

def trim_to_sentence(text):
    return '. '.join(text.split('. ')[:2]).strip()


#def generate_swot_pdf(swot, company_name="SWOT Report"):
 #   pdf = FPDF()
  #  pdf.set_auto_page_break(auto=True, margin=15)
   # pdf.add_page()
    #pdf.set_font("Arial", 'B', 16)
    #pdf.cell(0, 10, clean_text(f"{company_name} - SWOT Analysis"), ln=True)

    #pdf.set_font("Arial", '', 12)
    #for section, bullets in swot.items():
     #   pdf.ln(5)
      #  pdf.set_font("Arial", 'B', 14)
       # pdf.cell(0, 10, clean_text(section), ln=True)
        #pdf.set_font("Arial", '', 12)
        #for bullet in bullets:
         #   pdf.multi_cell(0, 8, clean_text(f"- {bullet['point']}"))
          #  pdf.set_text_color(100)
           # pdf.multi_cell(0, 6, clean_text(f"   -> {trim_to_sentence(bullet['support'])}"))
            #implication = bullet.get("implication")
            #if implication:
             #   pdf.multi_cell(0, 6, clean_text(f"   📍 {trim_to_sentence(implication)}"))
            #pdf.set_text_color(0)

    #return pdf.output(dest='S').encode('latin-1')
from fpdf import FPDF
from utils import clean_text, trim_to_sentence

def generate_swot_pdf(swot, company_name="SWOT Report"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text(f"{company_name} - SWOT Analysis"), ln=True)

    pdf.set_font("Arial", '', 12)
    for section, bullets in swot.items():
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, clean_text(section), ln=True)
        pdf.set_font("Arial", '', 12)

        for bullet in bullets:
            # Bullet point
            pdf.set_text_color(0)
            pdf.multi_cell(0, 8, clean_text(f"• {bullet['point']}"))

            # Supporting quote (add space and italics for separation)
            pdf.set_text_color(100)
            pdf.set_font("Arial", 'I', 11)
            pdf.multi_cell(0, 6, clean_text(f"📌 {trim_to_sentence(bullet['support'])}"))

            # Extra spacing between bullets
            pdf.ln(2)

        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0)

    return pdf.output(dest='S').encode('latin-1')

def generate_summary(swot_dict):
    summary = []
    summary.append("## SWOT Summary\n")

    for section, bullets in swot_dict.items():
        summary.append(f"\n### {section}")
        if bullets:
            for point in bullets:
                summary.append(f"- {point['point']}")
                summary.append(f"  📌 {point['support']}")
        else:
            summary.append("- No insights extracted.")

    return "\n".join(summary)



