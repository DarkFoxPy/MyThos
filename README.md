# Mythos

Sistema multi-agente para la gestión inteligente del período de prueba laboral.

Mythos acompaña los 60 días del período de prueba legal estructurando rutas de inducción a partir de los documentos corporativos de cada empresa, asistiendo al empleado nuevo mediante un asistente conversacional fundamentado en RAG, y entregando al supervisor un diagnóstico multidimensional de comprensión con alertas tempranas para sustentar la decisión de confirmación al día sesenta.

## Arquitectura

Sistema multi-agente con cuatro agentes especializados:

- **Athena** — Orquestador. Coordina el flujo entre agentes y dispara alertas al panel del supervisor.
- **Atlas** — Documentos y RAG. Indexa documentos corporativos, responde consultas fundamentadas y propone la ruta de inducción.
- **Apollo** — Clasificador de intención. Enruta las consultas del empleado según su tipo.
- **Artemis** — Diagnóstico. Genera cuestionarios aplicados, califica respuestas abiertas y produce el diagnóstico multidimensional cruzando tiempo, consultas y resultado.

## Stack

- **Lenguaje:** Python 3.12
- **Frontend:** Streamlit
- **Base de datos:** PostgreSQL (Supabase) con pgvector
- **Autenticación:** Supabase Auth (JWT + Row Level Security)
- **Almacenamiento:** Supabase Storage
- **LLM:** Google Gemini 2.5 Flash Lite
- **Embeddings:** gemini-embedding-001 (768 dimensiones)

## Estructura del proyecto

```
Mythos/
├── app.py                  # Punto de entrada Streamlit
├── config.py               # Carga de variables de entorno y constantes
├── requirements.txt
├── agents/
│   ├── athena.py           # Orquestador
│   ├── atlas.py            # RAG y rutas
│   ├── apollo.py           # Clasificación de intención
│   └── artemis.py          # Diagnóstico y cuestionarios
├── database/
│   ├── client.py           # Cliente Supabase
│   ├── schema.sql          # Esquema de la base de datos
│   └── wipe_data.sql       # Limpieza de datos para entornos de prueba
├── pages/
│   ├── login.py
│   ├── admin.py
│   ├── supervisor.py
│   └── employee.py
└── utils/
    ├── i18n.py             # Internacionalización (es / en)
    ├── llm.py              # Wrapper de Gemini
    ├── processor.py        # Procesamiento de documentos (PDF / DOCX)
    └── theme.py
```

## Configuración local

1. Clonar el repositorio.

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux / Mac
   source venv/bin/activate
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

   ```
   GEMINI_API_KEY=tu_clave_de_gemini
   SUPABASE_URL=tu_url_de_supabase
   SUPABASE_KEY=tu_anon_key_de_supabase
   ```

   - `GEMINI_API_KEY`: obtener en https://aistudio.google.com/apikey
   - `SUPABASE_URL` y `SUPABASE_KEY`: obtener en el dashboard del proyecto Supabase, sección Settings → API.

5. Aplicar el esquema de la base de datos sobre tu instancia de Supabase ejecutando `database/schema.sql` desde el SQL Editor del dashboard.

6. Ejecutar la aplicación:

   ```bash
   streamlit run app.py
   ```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `GEMINI_API_KEY` | Clave de API de Google Gemini |
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_KEY` | Anon key del proyecto Supabase |

El archivo `.env` está excluido del repositorio por `.gitignore` y nunca debe commitearse.

## Roles del sistema

- **Administrador (RRHH):** carga documentos corporativos, genera y aprueba la ruta de inducción.
- **Supervisor:** monitorea el equipo, recibe alertas y toma la decisión del día sesenta.
- **Empleado:** recorre la ruta, consulta al asistente y responde cuestionarios.

## Licencia

Proyecto académico — Universidad de la Integración de las Américas, Facultad de Ingeniería, Carrera de Ingeniería Informática y Sistemas. Curso de Proyecto de Sistemas Inteligentes.
