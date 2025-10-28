import io
import re
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st
from openpyxl import load_workbook


# ==========================================================
# 🔧 CONFIGURATION
# ==========================================================
st.set_page_config(page_title="🛢️ Primo Drilling Report", layout="wide")
TEMPLATE_PATH = "Daily Report Template.xlsx"  # Must exist in app directory


# ==========================================================
# 🔹 Utility Functions
# ==========================================================
def to_float(x):
    """Convert text or numbers safely to float."""
    if x is None or (isinstance(x, str) and x.strip() == ""):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).replace(",", " ").strip()
    m = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", s)
    return float(m[0]) if m else None


def to_str(x):
    """Convert any value to trimmed string."""
    return "" if x is None else str(x).strip()


def default_df(columns, rows=1):
    """Create an empty DataFrame with specified columns."""
    return pd.DataFrame([{c: None for c in columns} for _ in range(rows)])


def normalize_numeric(df):
    """Normalize numeric vs string columns for consistent deduping."""
    for col in df.columns:
        if any(
            k in col.lower()
            for k in [
                "ft", "hrs", "rpm", "psi", "qty", "no", "weight", "od", "id",
                "gpm", "spm", "size", "length", "depth", "bbl", "cum", "g_16"
            ]
        ):
            df[col] = df[col].map(to_float)
        else:
            df[col] = df[col].map(to_str)
    return df


def add_meta(df, core):
    """Attach core metadata columns to each exported table."""
    meta = pd.DataFrame([core] * max(len(df.index), 1))
    return pd.concat([meta.reset_index(drop=True), df.reset_index(drop=True)], axis=1)


def smart_dedupe(df, key_subset=None):
    """Robust deduplication with normalization and subset logic."""
    for c in df.columns:
        df[c] = df[c].apply(lambda x: str(x).strip().lower() if isinstance(x, str) else x)
    df = df.apply(lambda col: col.round(4) if pd.api.types.is_numeric_dtype(col) else col)
    if key_subset:
        return df.drop_duplicates(subset=key_subset, keep="first", ignore_index=True)
    return df.drop_duplicates(keep="first", ignore_index=True)


# ==========================================================
# ⚙️ STREAMLIT UI
# ==========================================================
st.title("🛢️ Primo Daily Drilling Report — Data Entry & Export")

# ---------------- Header ----------------
st.subheader("Header Information")
c1, c2, c3, c4 = st.columns(4)
report_number = c1.text_input("Report #", value="1")
report_date = c2.date_input("Date", value=datetime.today().date())
oil_company = c3.text_input("Oil Company", value="KIMMERIDGE TEXAS GAS")
contractor = c4.text_input("Contractor", value="Primo")

c5, c6, c7, c8 = st.columns(4)
well_name = c5.text_input("Well Name & No", value="HUFF A 106H")
location = c6.text_input("Location", value="MCMULLEN")
county_state = c7.text_input("County, State", value="TEXAS")
permit_no = c8.text_input("Permit Number", value="909899")

c9, c10 = st.columns(2)
api_number = c9.text_input("API #", value="42-311-37631")
rig_con_no = c10.text_input("Rig Contractor & No.", value="7")

# ---------------- Daily Progress ----------------
st.markdown("---")
st.subheader("Daily Progress")
c1, c2, c3, c4 = st.columns(4)
depth_0000 = c1.number_input("00:00 Depth (ft)", value=120.0)
depth_2400 = c2.number_input("24:00 Depth (ft)", value=288.0)
footage_today = c3.number_input("Footage Today (ft)", value=168.0)
rop_today = c4.number_input("ROP Today (ft/hr)", value=56.0)

c5, c6, c7, _ = st.columns(4)
drlg_hrs_today = c5.number_input("Drlg Hrs Today", value=3.0)
current_run_ftg = c6.number_input("Current Run Ftg", value=0.0)
circ_hrs_today = c7.number_input("Circ Hrs Today", value=0.0)

# ---------------- Tables ----------------
st.markdown("---")
colA, colB = st.columns(2)

with colA:
    st.subheader("Pump Data")
    pump_df = st.data_editor(
        default_df(
            ["pump_no", "bbls_per_stroke", "gals_per_stroke", "vol_gpm", "spm"], rows=2
        ).assign(pump_no=[1, 2]),
        num_rows="dynamic",
        key="pump",
    )

    st.subheader("Mud Data")
    mud_df = st.data_editor(default_df(["weight_ppg", "viscosity_sec", "pressure_psi"]), key="mud")

    st.subheader("Drilling Parameters & Motor")
    params_df = st.data_editor(
        default_df([
            "st_wt_rot_klbs", "pu_wt_klbs", "so_wt_klbs", "wob_klbs",
            "rotary_rpm", "motor_rpm", "total_bit_rpm", "rot_tq_off_btm_ftlb",
            "rot_tq_on_btm_ftlb", "off_bottom_pressure_psi", "on_bottom_pressure_psi"
        ]),
        key="params",
    )

    motor_df = st.data_editor(
        default_df([
            "run_no", "size_in", "type", "serial_no", "tool_deflection", "avg_diff_press_psi",
            "daily_drill_hrs", "daily_circ_hrs", "daily_total_hrs", "acc_drill_hrs", "acc_circ_hrs",
            "depth_in_ft", "depth_out_ft"
        ]),
        key="motor",
    )

with colB:
    st.subheader("BHA")
    bha_df = st.data_editor(
        default_df(
            ["item", "od_in", "id_in", "weight", "connection", "length_ft", "depth_ft"], rows=8
        ).assign(item=["BIT", "MOTOR", "UBHO", "MONEL", "SHOCK SUB", "8\" DC", "XO", "6\" DC"]),
        key="bha",
    )

    st.subheader("Survey Info (optional)")
    survey_df = st.data_editor(default_df(["depth_ft", "inc_deg", "azi_deg"], rows=3), key="survey")

# ---------------- Bit, Casing, Others ----------------
st.markdown("---")
st.subheader("Bit Data")
bit_df = st.data_editor(
    default_df([
        "no", "size_in", "mfg", "type", "nozzles_or_tfa", "serial_no", "depth_in_ft", "cum_footage_ft",
        "cum_hours", "depth_out_ft", "dull_ir", "dull_or", "dull_dc", "loc", "bs", "g_16", "oc", "rpld"
    ], rows=2),
    key="bit",
)

colC, colD, colE = st.columns(3)
with colC:
    st.subheader("Casing")
    casing_df = st.data_editor(
        default_df(["od_in", "id_in", "weight", "grade", "connection", "depth_set_ft"], rows=3), key="casing"
    )
with colD:
    st.subheader("Drill Pipe")
    drillpipe_df = st.data_editor(
        default_df(["od_in", "id_in", "weight", "grade", "connection"], rows=3), key="drillpipe"
    )
with colE:
    st.subheader("Rental Equipment")
    rental_df = st.data_editor(
        default_df(["item", "serial_no", "date_received", "date_returned"], rows=2), key="rental"
    )

st.subheader("Time Breakdown & Forecast")
time_df = st.data_editor(
    default_df(
        ["from_time", "to_time", "hrs", "start_depth_ft", "end_depth_ft", "cl", "description", "code", "forecast"],
        rows=6,
    ),
    key="timebk",
)

st.subheader("Fuel, Chemicals, Crew")
colF, colG = st.columns(2)
with colF:
    fuel_df = st.data_editor(
        default_df(["fuel_type", "vendor", "begin_qty", "received", "total", "used", "remaining"], rows=1)
        .assign(fuel_type="DIESEL"),
        key="fuel",
    )
    chemicals_df = st.data_editor(default_df(["additive", "qty", "unit"], rows=5), key="chems")

with colG:
    personnel_df = st.data_editor(default_df(["tour", "role", "name", "hours"], rows=8), key="people")


# ==========================================================
# 🚀 EXPORT & DOWNLOAD
# ==========================================================
if st.button("📦 Normalize, Dedupe & Export"):
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
        created_at=str(datetime.utcnow()),
    )

    dfs = [
        pump_df, mud_df, params_df, motor_df, bha_df, survey_df, bit_df,
        casing_df, drillpipe_df, rental_df, time_df, fuel_df, chemicals_df, personnel_df
    ]
    for df in dfs:
        normalize_numeric(df)

    outputs = {
        "core": pd.DataFrame([core]),
        "pump": add_meta(pump_df, core),
        "mud": add_meta(mud_df, core),
        "params": add_meta(params_df, core),
        "motor": add_meta(motor_df, core),
        "bha": add_meta(bha_df, core),
        "survey": add_meta(survey_df, core),
        "bit": add_meta(bit_df, core),
        "casing": add_meta(casing_df, core),
        "drillpipe": add_meta(drillpipe_df, core),
        "rental_equipment": add_meta(rental_df, core),
        "time_breakdown": add_meta(time_df, core),
        "fuel": add_meta(fuel_df, core),
        "chemicals": add_meta(chemicals_df, core),
        "personnel": add_meta(personnel_df, core),
    }

    # ✅ Smart deduping for all tables (key-based for pump & bha)
    dedupe_report = []
    for name, df in outputs.items():
        before = len(df)
        if name == "pump":
            df = smart_dedupe(df, key_subset=["report_number", "well_name", "pump_no"])
        elif name == "bha":
            df = smart_dedupe(df, key_subset=["report_number", "well_name", "item", "od_in"])
        else:
            df = smart_dedupe(df)
        after = len(df)
        outputs[name] = df
        if before != after:
            dedupe_report.append(f"{name}.csv → removed {before - after} duplicate rows")

    # --- Fill Excel Template ---
    try:
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

        filled_xlsx = io.BytesIO()
        wb.save(filled_xlsx)
        filled_xlsx.seek(0)
        st.download_button(
            "⬇️ Download Filled Excel Template",
            data=filled_xlsx.getvalue(),
            file_name=f"Drilling_Report_{report_number}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.warning(f"⚠️ Could not fill Excel template: {e}")
        filled_xlsx = None

    # --- ZIP export ---
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        for name, df in outputs.items():
            zf.writestr(f"{name}.csv", df.to_csv(index=False))
        if filled_xlsx:
            zf.writestr("filled_template.xlsx", filled_xlsx.getvalue())
    zip_buf.seek(0)

    st.download_button(
        "⬇️ Download All CSVs + Template (ZIP)",
        data=zip_buf.getvalue(),
        file_name=f"drilling_report_export_{report_date}.zip",
        mime="application/zip",
    )

    if dedupe_report:
        st.info("🧹 Duplicates Removed:\n" + "\n".join(dedupe_report))
    st.success("✅ Export complete! All files cleaned and deduped.")
