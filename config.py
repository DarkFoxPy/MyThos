import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")

# Modelo LLM — todos los agentes lo usan
GEMINI_MODEL       = "gemini-2.5-flash-lite"
EMBEDDING_MODEL    = "models/gemini-embedding-001"
EMBEDDING_DIM      = 768

# Procesamiento de documentos
CHUNK_SIZE    = 500   # palabras por fragmento
CHUNK_OVERLAP = 50    # solapamiento entre fragmentos

# RAG (Atlas)
RAG_THRESHOLD = 0.65  # similitud mínima para incluir un fragmento
RAG_TOP_K     = 5     # cantidad de fragmentos a recuperar

# Análisis de brechas (Artemis)
MIN_MODULE_TIME_RATIO = 0.3   # tiempo mínimo = 30% de duración estimada
BREACH_SCORE_THRESHOLD = 50   # quiz < 50% → brecha detectada
VERIFIED_SCORE_THRESHOLD = 70 # quiz >= 70% + tiempo ok → verificado
