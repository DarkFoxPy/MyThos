"""
Procesador de documentos — usado por Atlas para indexar el conocimiento corporativo.
Extrae texto de PDF/DOCX, divide en chunks y genera embeddings con Gemini.
"""
import io
import time
import math
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM, CHUNK_SIZE, CHUNK_OVERLAP

_client = genai.Client(api_key=GEMINI_API_KEY)

# El SDK nuevo espera el nombre sin el prefijo "models/"
_EMB_MODEL = EMBEDDING_MODEL.replace("models/", "")


def _embed(text: str, task_type: str) -> list[float]:
    """Genera embedding y garantiza que tenga EMBEDDING_DIM (768) dimensiones,
    normalizado para similitud coseno. gemini-embedding-001 devuelve 3072 por
    default; pedimos 768 explícitamente, y si la SDK no soporta el parámetro,
    truncamos + renormalizamos."""
    try:
        result = _client.models.embed_content(
            model=_EMB_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIM,
            ),
        )
    except TypeError:
        result = _client.models.embed_content(
            model=_EMB_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )

    emb = list(result.embeddings[0].values)
    if len(emb) > EMBEDDING_DIM:
        emb = emb[:EMBEDDING_DIM]
    elif len(emb) < EMBEDDING_DIM:
        emb = emb + [0.0] * (EMBEDDING_DIM - len(emb))

    norm = math.sqrt(sum(v * v for v in emb))
    if norm > 0:
        emb = [v / norm for v in emb]
    return emb


def extract_text(file_bytes: bytes, filename: str) -> str:
    fname = filename.lower()
    if fname.endswith(".pdf"):
        return _from_pdf(file_bytes)
    elif fname.endswith(".docx") or fname.endswith(".doc"):
        return _from_docx(file_bytes)
    raise ValueError(f"Formato no soportado: {filename}. Usá PDF o DOCX.")


def _from_pdf(file_bytes: bytes) -> str:
    import PyPDF2
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n\n".join(p.extract_text() or "" for p in reader.pages)


def _from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def split_into_chunks(text: str) -> list[str]:
    """Divide el texto en chunks de ~CHUNK_SIZE palabras con overlap."""
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        chunk = " ".join(words[start : start + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed_document(text: str) -> list[float]:
    return _embed(text, "RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    return _embed(text, "RETRIEVAL_QUERY")


def process_document(file_bytes: bytes, filename: str, document_id: str, company_id: str, db) -> int:
    """
    Pipeline completo de Atlas:
    1. Extrae texto del archivo
    2. Divide en chunks
    3. Genera embedding por chunk
    4. Guarda en pgvector (Supabase)
    Retorna el número de chunks procesados.
    """
    text = extract_text(file_bytes, filename)
    if not text.strip():
        raise ValueError("El documento está vacío o no pudo extraerse texto.")

    chunks = split_into_chunks(text)

    for i, chunk in enumerate(chunks):
        embedding = embed_document(chunk)
        db.table("document_chunks").insert({
            "document_id": document_id,
            "company_id":  company_id,
            "content":     chunk,
            "embedding":   embedding,
            "chunk_index": i,
        }).execute()
        time.sleep(0.08)  # respeta el rate limit de Gemini (15 req/min)

    db.table("documents").update({"processed": True}).eq("id", document_id).execute()
    return len(chunks)


def index_text(text: str, document_id: str, company_id: str, db) -> int:
    """
    Indexa texto plano ya existente (sin archivo de origen) en pgvector.
    Lo usa Quirón para incorporar el conocimiento capturado al supervisor
    como un documento más del RAG. Misma lógica que process_document pero
    partiendo de texto en vez de bytes.
    """
    if not text.strip():
        raise ValueError("El texto a indexar está vacío.")

    chunks = split_into_chunks(text)
    for i, chunk in enumerate(chunks):
        embedding = embed_document(chunk)
        db.table("document_chunks").insert({
            "document_id": document_id,
            "company_id":  company_id,
            "content":     chunk,
            "embedding":   embedding,
            "chunk_index": i,
        }).execute()
        time.sleep(0.08)

    db.table("documents").update({"processed": True}).eq("id", document_id).execute()
    return len(chunks)
