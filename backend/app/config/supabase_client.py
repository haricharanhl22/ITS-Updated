from supabase import create_client, Client

from app.config.settings import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)