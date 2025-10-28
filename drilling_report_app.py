import streamlit as st
import pandas as pd
import re, io, json, zipfile, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from supabase import create_client
from openpyxl import load_workbook

# ==============================
# 🔧 CONFIGURATION
# ==============================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_service_key"]
SMTP_SERVER = st.secrets["smtp_server"]
SMTP_PORT = int(st.secrets["smtp_port"])
SMTP_USER = st.secrets["smtp_user"]
SMTP_PASS = st.secrets["smtp_pass"]
TEMPLATE_PATH = "Daily Report Template.xlsx"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 🔹 Utility Functions
# ==============================
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

def ensure_cols(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]

def default_df(columns: list[str], rows: int = 1) -> pd.DataFrame:
    return pd.DataFrame([{c: None for c in columns} for _ in range(rows)])

def normalize_numeric(df: pd.DataFrame):
    for col in df.columns:
        if any(k in col.lower() for k in ["ft","hrs","rpm","psi","qty","no","weight","od","id","gpm","spm","size","length","depth","bbl","cum","g_16"]):
            df[col] = df[col].map(to_float)
        else:
            df[col] = df[col].map(to_str)
    return df

# ==============================
# ⚙️ Streamlit UI
# ==============================
st.set_page_config(page_title="🛢️ Daily Drilling Report — Data Entry & Export", layout="wide")
st.title("🛢️ Primo Daily Drilling Report — Full Entry & Automation")

email = st.text_input("📧 Enter your email to receive the formatted report:")
st.markdown("---")

# ---------------- Header Section ----------------
st.subheader("Header Information")
c1, c2, c3, c4 = st.columns(4)
report_number = c1.text_input("Report #", value="1")
report_date   = c2.date_input("Date", value=datetime.today().date())
oil_company   = c3.text_input("Oil Company", value="KIMMERIDGE TEXAS GAS")
contractor    = c4.text_input("Contractor", value="Primo")

c5, c6, c7, c8 = st.columns(4)
well_name     = c5.text_input("Well Name & No", value="HUFF A 106H")
location      = c6.text_input("Location", value="MCMULLEN")
county_state  = c7.text_input("County, State", value="TEXAS")
permit_no     = c8.text_input("Permit Number", value="909899")

c9, c10 = st.columns(2)
api_number    = c9.text_input("API #", value="42-311-37631")
rig_con_no    = c10.text_input("Rig Contractor & No.", value="7")

# ---------------- Daily Progress ----------------
st.markdown("---")
st.subheader("Daily Progress")
c1, c2, c3, c4 = st.columns(4)
depth_0000 = c1.number_input("00:00 Depth (ft)", value=120.0)
depth_2400 = c2.number_input("24:00 Depth (ft)", value=288.0)
footage_today = c3.number_input("Footage Today (ft)", value=168.0)
rop_today     = c4.number_input("ROP Today (ft/hr)", value=56.0)

c5, c6, c7, c8 = st.columns(4)
drlg_hrs_today = c5.number_input("Drlg Hrs Today", value=3.0)
current_run_ftg= c6.number_input("Current Run Ftg", value=0.0)
circ_hrs_today = c7.number_input("Circ Hrs Today", value=0.0)

# ---------------- Pump, Mud, Motor ----------------
st.markdown("---")
colA, colB = st.columns(2)

with colA:
    st.subheader("Pump Data")
    pump_cols = ["pump_no","bbls_per_stroke","gals_per_stroke","vol_gpm","spm"]
    pump_df = st.data_editor(default_df(pump_cols, rows=2).assign(pump_no=[1,2]), num_rows="dynamic", key="pump")

    st.subheader("Mud Data")
    mud_cols = ["weight_ppg","viscosity_sec","pressure_psi"]
    mud_df = st.data_editor(default_df(mud_cols), key="mud")

    st.subheader("Drilling Parameters & Motor")
    param_cols = ["st_wt_rot_klbs","pu_wt_klbs","so_wt_klbs","wob_klbs","rotary_rpm","motor_rpm","total_bit_rpm","rot_tq_off_btm_ftlb","rot_tq_on_btm_ftlb","off_bottom_pressure_psi","on_bottom_pressure_psi"]
    params_df = st.data_editor(default_df(param_cols), key="params")

    motor_cols = ["run_no","size_in","type","serial_no","tool_deflection","avg_diff_press_psi","daily_drill_hrs","daily_circ_hrs","daily_total_hrs","acc_drill_hrs","acc_circ_hrs","depth_in_ft","depth_out_ft"]
    motor_df = st.data_editor(default_df(motor_cols), key="motor")

with colB:
    st.subheader("BHA")
    bha_cols = ["item","od_in","id_in","weight","connection","length_ft","depth_ft"]
    bha_df = st.data_editor(default_df(bha_cols, rows=8).assign(item=["BIT","MOTOR","UBHO","MONEL","SHOCK SUB","8\" DC","XO","6\" DC"]), num_rows="dynamic", key="bha")

    st.subheader("Survey Info (optional)")
    survey_cols = ["depth_ft","inc_deg","azi_deg"]
    survey_df = st.data_editor(default_df(survey_cols, rows=3), key="survey")

# ---------------- Remaining Sections ----------------
st.markdown("---")
st.subheader("Bit Data")
bit_cols = ["no","size_in","mfg","type","nozzles_or_tfa","serial_no","depth_in_ft","cum_footage_ft","cum_hours","depth_out_ft","dull_ir","dull_or","dull_dc","loc","bs","g_16","oc","rpld"]
bit_df = st.data_editor(default_df(bit_cols, rows=2), key="bit")

colC, colD, colE = st.columns(3)
with colC:
    st.subheader("Casing")
    casing_cols = ["od_in","id_in","weight","grade","connection","depth_set_ft"]
    casing_df = st.data_editor(default_df(casing_cols, rows=3), key="casing")

with colD:
    st.subheader("Drill Pipe")
    dp_cols = ["od_in","id_in","weight","grade","connection"]
    drillpipe_df = st.data_editor(default_df(dp_cols, rows=3), key="drillpipe")

with colE:
    st.subheader("Rental Equipment")
    rental_cols = ["item","serial_no","date_received","date_returned"]
    rental_df = st.data_editor(default_df(rental_cols, rows=2), key="rental")

st.subheader("Time Breakdown & Forecast")
tb_cols = ["from_time","to_time","hrs","start_depth_ft","end_depth_ft","cl","description","code","forecast"]
time_df = st.data_editor(default_df(tb_cols, rows=6), key="timebk")

st.subheader("Fuel, Chemicals, Crew")
colF, colG = st.columns(2)
with colF:
    fuel_cols = ["fuel_type","vendor","begin_qty","received","total","used","remaining"]
    fuel_df = st.data_editor(default_df(fuel_cols, rows=1).assign(fuel_type="DIESEL"), key="fuel")

    chem_cols = ["additive","qty","unit"]
    chemicals_df = st.data_editor(default_df(chem_cols, rows=5), key="chems")

with colG:
    personnel_cols = ["tour","role","name","hours"]
    personnel_df = st.data_editor(default_df(personnel_cols, rows=8), key="people")

# ==============================
# 🚀 Normalize, Upload, & Email
# ==============================
if st.button("📤 Submit & Send Report"):
    core = dict(
        report_number=to_str(report_number),
        date=str(report_date),
        oil_company=to_str(oil_company),
        contractor=to_str(contractor),
        well_name=to_str(well_name),
        location=to_str(location),
        county_state=to_str(county_state),
        permit_number=to_str(permit_no),
        api_number=to_str(api_number),
        rig_contractor_no=to_str(rig_con_no),
        depth_0000_ft=to_float(depth_0000),
        depth_2400_ft=to_float(depth_2400),
        footage_today_ft=to_float(footage_today),
        rop_today_ft_hr=to_float(rop_today),
        drlg_hrs_today=to_float(drlg_hrs_today),
        current_run_ftg=to_float(current_run_ftg),
        circ_hrs_today=to_float(circ_hrs_today),
        created_at=str(datetime.utcnow())
    )

    def add_meta(df):
        meta = pd.DataFrame([core] * len(df.index))
        return pd.concat([meta.reset_index(drop=True), df.reset_index(drop=True)], axis=1)

    # Normalize all tables
    for df in [pump_df, mud_df, params_df, motor_df, bha_df, survey_df, bit_df, casing_df, drillpipe_df, rental_df, time_df, fuel_df, chemicals_df, personnel_df]:
        df[:] = normalize_numeric(df)

    outputs = {
        "core": pd.DataFrame([core]),
        "pump": add_meta(pump_df),
        "mud": add_meta(mud_df),
        "params": add_meta(params_df),
        "motor": add_meta(motor_df),
        "bha": add_meta(bha_df),
        "survey": add_meta(survey_df),
        "bit": add_meta(bit_df),
        "casing": add_meta(casing_df),
        "drillpipe": add_meta(drillpipe_df),
        "rental_equipment": add_meta(rental_df),
        "time_breakdown": add_meta(time_df),
        "fuel": add_meta(fuel_df),
        "chemicals": add_meta(chemicals_df),
        "personnel": add_meta(personnel_df)
    }

    # --- Upload to Supabase ---
    for name, df in outputs.items():
        try:
            data = json.loads(df.to_json(orient="records"))
            supabase.table(f"drilling_{name}").insert(data).execute()
        except Exception as e:
            st.warning(f"⚠️ Skipped {name}: {e}")

    st.success("✅ All data uploaded to Supabase!")

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

    # --- Email the formatted report ---
    if email:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = email
            msg["Subject"] = f"Daily Drilling Report #{report_number}"
            part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            part.set_payload(out_xlsx.getvalue())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=Drilling_Report_{report_number}.xlsx")
            msg.attach(part)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            st.success(f"📧 Report emailed to {email}")
        except Exception as e:
            st.error(f"Email send failed: {e}")

    st.download_button("⬇️ Download Filled Excel", data=out_xlsx.getvalue(), file_name=f"Drilling_Report_{report_number}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
