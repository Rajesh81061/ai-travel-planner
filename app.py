import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import os
import re
import requests

# ---------------- GEMINI CONFIG ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
UNSPLASH_KEY = st.secrets["UNSPLASH_ACCESS_KEY"]


model = genai.GenerativeModel(
    "gemini-flash-latest",
    generation_config={
        "temperature": 0.4,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 4600,
    }
)

st.set_page_config(page_title="AI Travel Planner", page_icon="🌍", layout="wide")

# ---------------- MAIN LAYOUT ----------------
left_col, right_col = st.columns([1.1, 2])

with left_col:
    st.image("travel.jpg", width=420)

with right_col:
    st.image("logo.png", width=100)

    st.markdown(
        "<h1 style='margin:0;padding:0;'>AI Travel Itinerary Generator ✈️🧳</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='margin-top:4px;margin-bottom:12px;font-size:17px;color:#00BFFF;font-style:italic;'>Pack Your Bags — We’ll Plan the Rest.</p>",
        unsafe_allow_html=True
    )

    destination = st.text_input("Enter Destination")
    days_input = st.text_input("Enter number of days")
    nights_input = st.text_input("Enter number of nights")
    generate_btn = st.button("✨ Generate Itinerary")

# ---------------- PROMPT ----------------
def build_prompt(dest, days, nights):
    return f"""
Create a detailed {days}-day {nights}-night travel itinerary for {dest}.

STRICT FORMAT RULES:

Day 1 Title

🌅 Morning:
Paragraph.

☀️ Afternoon:
Paragraph.

🌇 Evening:
Paragraph.

🌙 Night:
Paragraph.

Repeat for all {days} days.

Then provide:

✈️ Travel Tips:
• Tip 1
• Tip 2
• Tip 3

🍲 Food Recommendations:
• Dish 1
• Dish 2
• Dish 3

🏨 Hotel/Stay Suggestions:
• Hotel 1
• Hotel 2
• Hotel 3

IMPORTANT:
No markdown symbols like * or #
No tables
Use emojis exactly as shown
"""

# ---------------- TEXT CLEANING FOR PDF ----------------
def clean_text(text):
    text = re.sub(r"[#*]", "", text)

    replacements = {
        "–": "-",
        "—": "-",
        "’": "'",
        "“": '"',
        "”": '"',
        "•": "-",
        "→": "->",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    text = text.encode("latin-1", "ignore").decode("latin-1")
    return text.strip()

# ---------------- CUSTOM PDF CLASS ----------------
class PDF(FPDF):
    def footer(self):
        self.set_y(-10)
        self.set_font("Arial", size=9)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")

# ---------------- PDF CREATION ----------------
def create_pdf(text, destination):
    text = clean_text(text)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=12)

    # -------- COVER PAGE --------
    image_url = f"https://source.unsplash.com/1200x800/?{destination},travel"
    image_path = "/tmp/cover.jpg"

    try:
        img_data = requests.get(image_url, timeout=10).content
        with open(image_path, "wb") as handler:
            handler.write(img_data)

        pdf.add_page()
        pdf.image(image_path, x=0, y=0, w=210, h=297)

        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 26)
        pdf.ln(120)
        pdf.cell(0, 15, f"{destination.upper()} TRAVEL ITINERARY", align="C", ln=True)

        pdf.set_font("Arial", "", 14)
        pdf.cell(0, 10, "AI Generated Personalized Plan", align="C", ln=True)

        os.remove(image_path)
    except:
        pass

    # -------- ITINERARY PAGES --------
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, f"{destination} Travel Itinerary", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", size=11)

    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("✈️") or stripped.startswith("🍲") or stripped.startswith("🏨"):
            pdf.ln(5)
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(0, 8, stripped)
            pdf.ln(2)
            pdf.set_font("Arial", size=11)

        elif stripped.startswith("-"):
            pdf.multi_cell(0, 6, stripped)
            pdf.ln(1)

        elif stripped.lower().startswith("day"):
            pdf.ln(4)
            pdf.set_font("Arial", "B", 13)
            pdf.multi_cell(0, 7, stripped)
            pdf.ln(1)
            pdf.set_font("Arial", size=11)

        else:
            pdf.multi_cell(0, 6, stripped)

    pdf_path = "travel_itinerary.pdf"
    pdf.output(pdf_path)
    return pdf_path

# ---------------- GENERATE ITINERARY ----------------
if generate_btn:
    if not destination or not days_input or not nights_input:
        st.warning("⚠️ Please fill all the fields before generating itinerary.")
    elif not days_input.isdigit() or not nights_input.isdigit():
        st.warning("⚠️ Days and Nights must be valid numbers.")
    else:
        days = int(days_input)
        nights = int(nights_input)

        with st.spinner("Generating your travel plan... ✈️"):
            prompt = build_prompt(destination, days, nights)
            response = model.generate_content(prompt)
            st.session_state.itinerary = response.text
            st.session_state.destination = destination

# ---------------- DISPLAY RESULT ----------------
if "itinerary" in st.session_state:
    st.markdown(st.session_state.itinerary)

    pdf_path = create_pdf(st.session_state.itinerary, st.session_state.destination)
    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download Itinerary as PDF",
            f,
            file_name="travel_itinerary.pdf",
            mime="application/pdf"
        )


