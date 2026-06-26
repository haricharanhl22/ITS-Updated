import sys
from supabase import create_client
from app.config.settings import settings

print("Supabase package path:", sys.modules.get("supabase"))
client = create_client(settings.supabase_url, settings.supabase_key)
print("Postgrest client:", client.postgrest)
print("Has auth method:", hasattr(client.postgrest, "auth"))
if hasattr(client.postgrest, "auth"):
    print("auth signature:", client.postgrest.auth)
