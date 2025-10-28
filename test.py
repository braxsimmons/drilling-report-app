from supabase import create_client

url = "https://nwmnfplwvxvkelcqaiay.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53bW5mcGx3dnh2a2VsY3FhaWF5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDcxNzgzNCwiZXhwIjoyMDc2MjkzODM0fQ.NUzc_vdG-zsZIBoA90qCtOnU6baS17N0g7Wt7gBCN3M"

supabase = create_client(url, key)
print(supabase.table("drilling_core").select("*").limit(1).execute())

