from supabase import create_client

url = "https://nwmnfplwvxvkelcqaiay.supabase.co"
key = "sb_secret_No71cZiZAt_XFSW9XBneoA_8xiChYWC"
supabase = create_client(url, key)

record = {
    "report_number": "TEST-001",
    "date": "2025-10-28",
    "oil_company": "Test Energy Inc.",
    "contractor": "Primo",
    "well_name": "HUFF A 106H",
    "location": "MCMULLEN",
    "county_state": "TEXAS",
    "permit_number": "999999",
    "api_number": "42-000-00000",
    "rig_contractor_no": "7",
    "depth_0000_ft": 100,
    "depth_2400_ft": 200,
    "footage_today_ft": 100,
    "rop_today_ft_hr": 50,
    "drlg_hrs_today": 2,
    "current_run_ftg": 50,
    "circ_hrs_today": 0.5,
    "created_at": "2025-10-28T12:00:00Z"
}

res = supabase.table("drilling_core").insert(record).execute()
print(res)
