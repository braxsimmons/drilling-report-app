import streamlit as st
import pandas as pd
import re, io, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from supabase import create_client
from openpyxl import load_workbook

# --- ⚙️ Load secrets ---
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_service_key"]
SMTP_SERVER = st.secrets["smtp_server"]
SMTP_PORT = int(st.secrets["smtp_port"])
SMTP_USER = st.secrets["smtp_user"]
SMTP_PASS = st.secrets["smtp_pass"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TEMPLATE_PATH = "Daily Report Template.xlsx"

# --- 🔹 Utility functions ---
def to_float(x):
    if x is None or (isinstance(x, str) and x.strip() == ""):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).replace(",", " ").strip()
    m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", s)
    return float(m[0]) if m else None

def to_str(x): 
    return "" if x is None else str(x).strip()

# --- 🧱 Streamlit UI ---
st.set_page_config(page_title="🛢️ Primo Daily Drilling Report", layout="wide")
st.title("🛢️ Primo Daily Drilling Report")

st.markdown("### Report Info")
email = st.text_input("Recipient Email (for report delivery)")
report_number = st.text_input("Report #", value="1")
report_date = st.date_input("Date", value=datetime.today().date())
well_name = st.text_input("Well Name & No", value="HUFF A 106H")
contractor = st.text_input("Contractor", value="Primo")
location = st.text_input("Location", value="MCMULLEN")
depth_0000 = st.number_input("00:00 Depth (ft)", value=120.0)
depth_2400 = st.number_input("24:00 Depth (ft)", value=288.0)
footage_today = st.number_input("Footage Today (ft)", value=168.0)
drlg_hrs_today = st.number_input("Drlg Hrs Today", value=3.0)

if st.button("📤 Submit Report"):
    try:
        # --- Build Core Record ---
        core = {
            "report_number": report_number,
            "date": str(report_date),
            "well_name": well_name,
            "contractor": contractor,
            "location": location,
            "depth_0000_ft": to_float(depth_0000),
            "depth_2400_ft": to_float(depth_2400),
            "footage_today_ft": to_float(footage_today),
            "drlg_hrs_today": to_float(drlg_hrs_today),
            "created_at": datetime.utcnow().isoformat()
        }

        # --- Push to Supabase ---
        res = supabase.table("drilling_core").insert(core).execute()
        if res.data:
            st.success("✅ Data successfully uploaded to Supabase!")

        # --- Fill Excel Template ---
        wb = load_workbook(TEMPLATE_PATH, keep_vba=True)
        ws = wb.active
        ws["B2"] = core["report_number"]
        ws["E2"] = core["date"]
        ws["B4"] = core["well_name"]
        ws["B5"] = core["location"]
        ws["B8"] = core["contractor"]
        ws["C12"] = core["depth_0000_ft"]
        ws["C13"] = core["depth_2400_ft"]
        ws["E12"] = core["footage_today_ft"]
        ws["E13"] = core["drlg_hrs_today"]

        out_xlsx = io.BytesIO()
        wb.save(out_xlsx)
        out_xlsx.seek(0)

        # --- Email the report ---
        if email:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = email
            msg["Subject"] = f"Daily Drilling Report #{report_number}"

            part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            part.set_payload(out_xlsx.getvalue())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=Drilling_Report_{report_number}.xlsx"
            )
            msg.attach(part)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)

            st.success(f"📧 Report emailed to {email}")
        else:
            st.warning("No email entered — skipping email send.")

        # --- Local Download Option ---
        st.download_button(
            "⬇️ Download Filled Excel",
            data=out_xlsx.getvalue(),
            file_name=f"Drilling_Report_{report_number}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
