import sys
sys.path.append(r'c:\Users\91779\Desktop\AMS\HCAI-ITS\backend')

from app.config.supabase_client import supabase

def run_sql_file(filepath: str):
    with open(filepath, 'r') as f:
        query = f.read()
    try:
        res = supabase.rpc("exec_sql", {"sql_query": query}).execute()
        print("Success:", res.data)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run_sql_file(r'c:\Users\91779\Desktop\AMS\HCAI-ITS\scratch\update_rls.sql')
