from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


def get_client(access_token: str = None) -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Faltan SUPABASE_URL y SUPABASE_KEY en el .env")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if access_token:
        client.postgrest.auth(access_token)
    return client
