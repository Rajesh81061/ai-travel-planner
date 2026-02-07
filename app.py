import streamlit as st
import google.generativeai as genai
import pdfkit
import os
import re

# ---------------- GEMINI CONFIG (UNCHANGED) ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel(
    "gemini-flash-latest",
    generation_config={
        "temperature": 0.4,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 4600,
    }
)

# ---------------- WKHTMLTOPDF CONFIG ----------------
path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

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

    form_left, form_right = st.columns([3, 2])

    with form_left:
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

# ---------------- CLEAN TEXT ----------------
def clean_text(text):
    return re.sub(r"[#*]", "", text).strip()

# ---------------- PDF CREATION ----------------
def create_pdf(text):
    logo_path = os.path.abspath("logo.png")
    text = clean_text(text)
    html_text = text.replace("\n", "<br>")

    html_content = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 50px;
            line-height: 1.6;
        }}
        .logo {{
            text-align:center;
            margin-bottom: 12px;
        }}
        h1 {{
            text-align:center;
        }}
    </style>
    </head>
    <body>
        <div class="logo">
            <img src="file:///{logo_path}" width="110">
        </div>
        <h1>Travel Itinerary</h1>
        <div>{html_text}</div>
    </body>
    </html>
    """

    options = {
        'enable-local-file-access': None,
        'footer-center': 'Page [page]',
        'margin-bottom': '15mm'
    }

    pdf_file = "travel_itinerary.pdf"
    pdfkit.from_string(html_content, pdf_file, configuration=config, options=options)
    return pdf_file

# ---------------- GENERATE ----------------
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

# ---------------- DISPLAY RESULT ----------------
if "itinerary" in st.session_state:
    st.markdown(st.session_state.itinerary)

    pdf_path = create_pdf(st.session_state.itinerary)
    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download Itinerary as PDF",
            f,
            file_name="travel_itinerary.pdf",
            mime="application/pdf"
        )
