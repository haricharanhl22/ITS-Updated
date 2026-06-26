import sys
sys.path.append(r'c:\Users\91779\Desktop\AMS\HCAI-ITS\backend')

from app.config.supabase_client import supabase

queries = [
    "ALTER TABLE messages ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;",
    """CREATE POLICY "Users can insert their own messages" ON messages FOR INSERT WITH CHECK (student_id::uuid = auth.uid());""",
    """CREATE POLICY "Users can select their own messages" ON messages FOR SELECT USING (student_id::uuid = auth.uid());""",
    """CREATE POLICY "Users can insert their own learning events" ON learning_events FOR INSERT WITH CHECK (student_id::uuid = auth.uid());""",
    """CREATE POLICY "Users can select their own learning events" ON learning_events FOR SELECT USING (student_id::uuid = auth.uid());""",
    """CREATE POLICY "Users can insert their own mastery" ON student_mastery FOR INSERT WITH CHECK (student_id::uuid = auth.uid());""",
    """CREATE POLICY "Users can select their own mastery" ON student_mastery FOR SELECT USING (student_id::uuid = auth.uid());""",
    """CREATE POLICY "Users can update their own mastery" ON student_mastery FOR UPDATE USING (student_id::uuid = auth.uid()) WITH CHECK (student_id::uuid = auth.uid());"""
]

def run_sql():
    for q in queries:
        try:
            res = supabase.rpc("exec_sql", {"sql_query": q}).execute()
            print("Success:", q[:50])
        except Exception as e:
            print("Error on:", q[:50], "\n", e)

if __name__ == "__main__":
    run_sql()
