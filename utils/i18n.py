import streamlit as st

LANGS = ("es", "en", "pt")
DEFAULT_LANG = "es"

# Banderas SVG inline (cross-platform, no dependen de fuentes emoji)
FLAGS = {
    "es": """<svg viewBox="0 0 6 4" width="22" height="14"><rect width="6" height="4" fill="#AA151B"/><rect y="1" width="6" height="2" fill="#F1BF00"/></svg>""",
    "en": """<svg viewBox="0 0 19 10" width="22" height="14"><rect width="19" height="10" fill="#FFFFFF"/><rect y="0" width="19" height="0.77" fill="#B22234"/><rect y="1.54" width="19" height="0.77" fill="#B22234"/><rect y="3.08" width="19" height="0.77" fill="#B22234"/><rect y="4.62" width="19" height="0.77" fill="#B22234"/><rect y="6.16" width="19" height="0.77" fill="#B22234"/><rect y="7.70" width="19" height="0.77" fill="#B22234"/><rect y="9.23" width="19" height="0.77" fill="#B22234"/><rect width="7.6" height="5.4" fill="#3C3B6E"/></svg>""",
    "pt": """<svg viewBox="0 0 14 10" width="22" height="14"><rect width="14" height="10" fill="#009C3B"/><polygon points="7,1 13,5 7,9 1,5" fill="#FFDF00"/><circle cx="7" cy="5" r="2" fill="#002776"/></svg>""",
}

LANG_LABELS = {"es": "Español", "en": "English", "pt": "Português"}


T = {
    # ── Sidebar ──
    "sidebar.active_agents":   {"es": "Agentes activos",        "en": "Active agents",         "pt": "Agentes ativos"},
    "sidebar.signout":         {"es": "Cerrar sesión",          "en": "Sign out",              "pt": "Sair"},
    "sidebar.role.admin":      {"es": "Administrador",          "en": "Administrator",         "pt": "Administrador"},
    "sidebar.role.supervisor": {"es": "Supervisor",             "en": "Supervisor",            "pt": "Supervisor"},
    "sidebar.role.employee":   {"es": "Empleado",               "en": "Employee",              "pt": "Funcionário"},

    # ── Auth / Login ──
    "auth.signin":             {"es": "Iniciar sesión",         "en": "Sign in",               "pt": "Entrar"},
    "auth.register":           {"es": "Registrarse",            "en": "Register",              "pt": "Cadastrar-se"},
    "auth.email":              {"es": "Correo electrónico",     "en": "Email",                 "pt": "E-mail"},
    "auth.password":           {"es": "Contraseña",             "en": "Password",              "pt": "Senha"},
    "auth.submit":             {"es": "Ingresar",               "en": "Sign in",               "pt": "Entrar"},
    "auth.fill_all":           {"es": "Completá todos los campos.", "en": "Fill in all fields.", "pt": "Preencha todos os campos."},
    "auth.invalid":            {"es": "Correo o contraseña incorrectos.", "en": "Incorrect email or password.", "pt": "E-mail ou senha incorretos."},
    "auth.no_company":         {"es": "Tu cuenta no tiene empresa asignada. Contactá al administrador.",
                                 "en": "Your account has no company assigned. Contact the administrator.",
                                 "pt": "Sua conta não tem empresa atribuída. Entre em contato com o administrador."},
    "auth.network_err":        {"es": "Error de red",           "en": "Network error",         "pt": "Erro de rede"},
    "auth.error":              {"es": "Error",                  "en": "Error",                 "pt": "Erro"},
    "auth.error_code":         {"es": "Código",                 "en": "Code",                  "pt": "Código"},
    "auth.full_name":          {"es": "Nombre completo",        "en": "Full name",             "pt": "Nome completo"},
    "auth.company_id":         {"es": "ID de empresa",          "en": "Company ID",            "pt": "ID da empresa"},
    "auth.role":               {"es": "Rol",                    "en": "Role",                  "pt": "Função"},
    "auth.create_account":     {"es": "Crear cuenta",           "en": "Create account",        "pt": "Criar conta"},
    "auth.account_created":    {"es": "Cuenta creada. Ya podés iniciar sesión.",
                                 "en": "Account created. You can sign in now.",
                                 "pt": "Conta criada. Você já pode entrar."},
    "auth.need_company_id":    {"es": "Necesitás el ID de tu empresa para registrarte. Pedíselo al administrador.",
                                 "en": "You need your company ID to register. Request it from the administrator.",
                                 "pt": "Você precisa do ID da sua empresa para se cadastrar. Solicite ao administrador."},
    "auth.invalid_company":    {"es": "ID de empresa inválido.", "en": "Invalid company ID.",  "pt": "ID de empresa inválido."},
    "auth.role_employee_only": {"es": "Todo nuevo usuario se registra como empleado. La asignación de roles supervisor o administrador la realiza únicamente el administrador de Recursos Humanos desde su panel.",
                                 "en": "Every new user signs up as employee. Supervisor or administrator roles can only be assigned by the Human Resources administrator from their panel.",
                                 "pt": "Todo novo usuário se cadastra como funcionário. A atribuição dos papéis de supervisor ou administrador é feita apenas pelo administrador de Recursos Humanos no seu painel."},

    # ── Admin ──
    "admin.title":             {"es": "Administración",         "en": "Administration",        "pt": "Administração"},
    "admin.subtitle":          {"es": "Documentos · Ruta de onboarding · Empresa",
                                 "en": "Documents · Onboarding Route · Company",
                                 "pt": "Documentos · Trajeto de integração · Empresa"},
    "admin.tab.docs":          {"es": "Documentos",             "en": "Documents",             "pt": "Documentos"},
    "admin.tab.route":         {"es": "Ruta de onboarding",     "en": "Onboarding Route",      "pt": "Trajeto de integração"},
    "admin.tab.company":       {"es": "Empresa",                "en": "Company",               "pt": "Empresa"},
    "admin.docs.title":        {"es": "Índice documental",      "en": "Document Index",        "pt": "Índice de documentos"},
    "admin.docs.desc":         {"es": "Subí documentos corporativos. Atlas los va a fragmentar e incorporar al vector store. Una vez procesados, los empleados pueden consultar cualquier información a través del asistente.",
                                 "en": "Upload corporate documents. Atlas will chunk and embed them into the vector store. Once processed, employees can query any information through the assistant.",
                                 "pt": "Envie documentos corporativos. O Atlas vai dividir e incorporar ao banco vetorial. Uma vez processados, os funcionários podem consultar qualquer informação através do assistente."},
    "admin.docs.process":      {"es": "Procesar con Atlas",     "en": "Process with Atlas",    "pt": "Processar com Atlas"},
    "admin.docs.indexing":     {"es": "Atlas indexando",        "en": "Atlas indexing",        "pt": "Atlas indexando"},
    "admin.docs.fragments":    {"es": "fragmentos indexados",   "en": "fragments indexed",     "pt": "fragmentos indexados"},
    "admin.docs.indexed":      {"es": "Documentos indexados",   "en": "Indexed Documents",     "pt": "Documentos indexados"},
    "admin.docs.processed":    {"es": "Procesado",              "en": "Processed",             "pt": "Processado"},
    "admin.docs.pending":      {"es": "Pendiente",              "en": "Pending",               "pt": "Pendente"},
    "admin.docs.empty":        {"es": "Sin documentos aún. Subí el reglamento interno, manuales de procedimiento, etc.",
                                 "en": "No documents yet. Upload internal regulations, procedure manuals, etc.",
                                 "pt": "Sem documentos ainda. Envie regulamentos internos, manuais de procedimento, etc."},
    "admin.route.title":       {"es": "Ruta de onboarding",     "en": "Onboarding Route",      "pt": "Trajeto de integração"},
    "admin.route.desc":        {"es": "Atlas analiza los documentos y propone una secuencia de aprendizaje. Revisá, ajustá y activá con Athena.",
                                 "en": "Atlas analyzes documents and proposes a learning sequence. Review, adjust and activate with Athena.",
                                 "pt": "O Atlas analisa documentos e propõe uma sequência de aprendizado. Revise, ajuste e ative com Athena."},
    "admin.route.generate":    {"es": "Generar ruta con Atlas", "en": "Generate route with Atlas", "pt": "Gerar trajeto com Atlas"},
    "admin.route.analyzing":   {"es": "Atlas analizando documentos...", "en": "Atlas analyzing documents...", "pt": "Atlas analisando documentos..."},
    "admin.route.proposed":    {"es": "módulos propuestos.",    "en": "modules proposed.",     "pt": "módulos propostos."},
    "admin.route.proposal":    {"es": "Propuesta de Atlas — editá antes de aprobar",
                                 "en": "Atlas Proposal — edit before approving",
                                 "pt": "Proposta do Atlas — edite antes de aprovar"},
    "admin.route.title_label": {"es": "Título",                 "en": "Title",                 "pt": "Título"},
    "admin.route.topic":       {"es": "Tema",                   "en": "Topic",                 "pt": "Tema"},
    "admin.route.duration":    {"es": "Duración (min)",         "en": "Duration (min)",        "pt": "Duração (min)"},
    "admin.route.approve":     {"es": "Aprobar y activar con Athena", "en": "Approve and activate with Athena", "pt": "Aprovar e ativar com Athena"},
    "admin.route.activating":  {"es": "Activando ruta...",      "en": "Activating route...",   "pt": "Ativando trajeto..."},
    "admin.route.active":      {"es": "Ruta activa",            "en": "Active Route",          "pt": "Trajeto ativo"},
    "admin.route.no_active":   {"es": "Sin ruta activa. Generá una arriba.",
                                 "en": "No active route. Generate one above.",
                                 "pt": "Sem trajeto ativo. Gere um acima."},
    "admin.route.module_n":    {"es": "Módulo",                 "en": "Module",                "pt": "Módulo"},
    "admin.route.active_route":{"es": "Ruta activa con",        "en": "Route active with",     "pt": "Trajeto ativo com"},
    "admin.route.modules":     {"es": "módulos.",               "en": "modules.",              "pt": "módulos."},
    "admin.company.title":     {"es": "Empresa",                "en": "Company",               "pt": "Empresa"},
    "admin.company.id_label":  {"es": "ID de empresa",          "en": "Company ID",            "pt": "ID da empresa"},
    "admin.company.id_desc":   {"es": "Compartí este ID con tus empleados para que puedan registrar sus cuentas.",
                                 "en": "Share this ID with employees so they can register their accounts.",
                                 "pt": "Compartilhe este ID com seus funcionários para que possam cadastrar suas contas."},
    "admin.company.users":     {"es": "Usuarios registrados",   "en": "Registered Users",      "pt": "Usuários cadastrados"},
    "admin.company.roles_help":{"es": "Solo el administrador de Recursos Humanos puede modificar los roles. Los nuevos usuarios se registran siempre como empleados y desde acá podés promoverlos a supervisor o administrador cuando corresponda. El cambio impacta en cuanto el usuario cierre y vuelva a iniciar sesión.",
                                 "en": "Only the Human Resources administrator can change roles. New users always register as employees and from here you can promote them to supervisor or administrator when appropriate. The change takes effect once the user logs out and signs in again.",
                                 "pt": "Apenas o administrador de Recursos Humanos pode alterar os papéis. Novos usuários sempre se cadastram como funcionários e a partir daqui você pode promovê-los a supervisor ou administrador quando for o caso. A alteração entra em vigor após o usuário sair e fazer login novamente."},
    "admin.company.save_role": {"es": "Aplicar",                "en": "Apply",                 "pt": "Aplicar"},

    # ── Employee ──
    "emp.welcome":             {"es": "Bienvenido",             "en": "Welcome",               "pt": "Bem-vindo"},
    "emp.subtitle":            {"es": "Ruta de onboarding · Asistente",
                                 "en": "Onboarding route · Assistant",
                                 "pt": "Trajeto de integração · Assistente"},
    "emp.tab.route":           {"es": "Mi ruta",                "en": "My Route",              "pt": "Meu trajeto"},
    "emp.tab.assistant":       {"es": "Asistente",              "en": "Assistant",             "pt": "Assistente"},
    "emp.tab.docs":            {"es": "Documentos",             "en": "Documents",             "pt": "Documentos"},
    "emp.docs.title":          {"es": "Documentación oficial",  "en": "Official documentation","pt": "Documentação oficial"},
    "emp.docs.desc":           {"es": "Estos son los documentos oficiales que cargó tu empresa. De acá sale cada módulo de tu ruta. Leélos como material de estudio; el asistente responde fundamentándose en ellos.",
                                 "en": "These are the official documents your company uploaded. Every module in your route comes from them. Read them as study material; the assistant answers grounded in them.",
                                 "pt": "Estes são os documentos oficiais que sua empresa enviou. Cada módulo do seu trajeto vem deles. Leia-os como material de estudo; o assistente responde com base neles."},
    "emp.docs.empty":          {"es": "Tu empresa todavía no cargó documentos. El administrador los va a subir pronto.",
                                 "en": "Your company hasn't uploaded documents yet. The administrator will upload them soon.",
                                 "pt": "Sua empresa ainda não enviou documentos. O administrador os enviará em breve."},
    "emp.docs.read":           {"es": "Leer documento",         "en": "Read document",         "pt": "Ler documento"},
    "emp.docs.source":         {"es": "Material oficial del módulo", "en": "Module's official material", "pt": "Material oficial do módulo"},
    "emp.module.locked":       {"es": "Completá el módulo anterior para desbloquear este.",
                                 "en": "Complete the previous module to unlock this one.",
                                 "pt": "Conclua o módulo anterior para desbloquear este."},
    "emp.route.not_ready":     {"es": "Tu ruta de onboarding todavía no está lista. El administrador la está preparando.",
                                 "en": "Your onboarding route is not ready yet. The administrator is setting it up.",
                                 "pt": "Seu trajeto de integração ainda não está pronto. O administrador está preparando."},
    "emp.modules":             {"es": "módulos",                "en": "modules",               "pt": "módulos"},
    "emp.module":              {"es": "Módulo",                 "en": "Module",                "pt": "Módulo"},
    "emp.topic":               {"es": "Tema",                   "en": "Topic",                 "pt": "Tema"},
    "emp.estimated":           {"es": "Duración estimada",      "en": "Estimated duration",    "pt": "Duração estimada"},
    "emp.time_logged":         {"es": "Tiempo registrado",      "en": "Time logged",           "pt": "Tempo registrado"},
    "emp.quiz":                {"es": "Quiz",                   "en": "Quiz",                  "pt": "Quiz"},
    "emp.start_module":        {"es": "Iniciar módulo",         "en": "Start module",          "pt": "Iniciar módulo"},
    "emp.time_spent":          {"es": "Tiempo dedicado (min)",  "en": "Time spent (min)",      "pt": "Tempo dedicado (min)"},
    "emp.save_time":           {"es": "Guardar tiempo",         "en": "Save time",             "pt": "Salvar tempo"},
    "emp.take_quiz":           {"es": "Hacer quiz de Artemis",  "en": "Take Artemis quiz",     "pt": "Fazer quiz da Artemis"},
    "emp.quiz.title":          {"es": "Evaluación de Artemis",  "en": "Artemis Evaluation",    "pt": "Avaliação de Artemis"},
    "emp.quiz.desc":           {"es": "Respondé con tus propias palabras. Artemis evalúa comprensión real, no memorización.",
                                 "en": "Answer in your own words. Artemis evaluates real comprehension, not memorization.",
                                 "pt": "Responda com suas próprias palavras. Artemis avalia compreensão real, não memorização."},
    "emp.quiz.generating":     {"es": "Artemis generando preguntas...", "en": "Artemis generating questions...", "pt": "Artemis gerando perguntas..."},
    "emp.quiz.your_answer":    {"es": "Tu respuesta",           "en": "Your answer",           "pt": "Sua resposta"},
    "emp.quiz.submit":         {"es": "Enviar",                 "en": "Submit",                "pt": "Enviar"},
    "emp.quiz.write_first":    {"es": "Escribí tu respuesta antes de enviar.", "en": "Write your answer before submitting.", "pt": "Escreva sua resposta antes de enviar."},
    "emp.quiz.evaluating":     {"es": "Artemis evaluando...",   "en": "Artemis evaluating...", "pt": "Artemis avaliando..."},
    "emp.quiz.score.correct":  {"es": "Correcto",               "en": "Correct",               "pt": "Correto"},
    "emp.quiz.score.partial":  {"es": "Parcial",                "en": "Partial",               "pt": "Parcial"},
    "emp.quiz.score.incorrect":{"es": "Incorrecto",             "en": "Incorrect",             "pt": "Incorreto"},
    "emp.complete_module":     {"es": "Completar módulo y obtener diagnóstico de Artemis",
                                 "en": "Complete module and get Artemis diagnosis",
                                 "pt": "Concluir módulo e obter diagnóstico da Artemis"},
    "emp.analyzing":           {"es": "Artemis analizando tu progreso...", "en": "Artemis analyzing your progress...", "pt": "Artemis analisando seu progresso..."},
    "emp.diag.verified":       {"es": "Artemis verificó tu comprensión del módulo.",
                                 "en": "Artemis verified your comprehension of this module.",
                                 "pt": "Artemis verificou sua compreensão deste módulo."},
    "emp.diag.not_verified":   {"es": "Módulo completado. Hay margen para profundizar en algunos puntos.",
                                 "en": "Module complete. There is room to deepen some points.",
                                 "pt": "Módulo concluído. Há espaço para aprofundar em alguns pontos."},
    "emp.diag.breach":         {"es": "Se detectaron algunas brechas. Tu supervisor va a hacer seguimiento.",
                                 "en": "Some gaps were detected. Your supervisor will follow up.",
                                 "pt": "Algumas lacunas foram detectadas. Seu supervisor fará acompanhamento."},
    "emp.diag.complete":       {"es": "Módulo completado.",     "en": "Module complete.",      "pt": "Módulo concluído."},
    "emp.chat.related":        {"es": "Pregunta relacionada a", "en": "Question related to",   "pt": "Pergunta relacionada a"},
    "emp.chat.general":        {"es": "General (sin módulo específico)", "en": "General (no specific module)", "pt": "Geral (sem módulo específico)"},
    "emp.chat.first":          {"es": "Hacé tu primera pregunta. Podés escribir de manera informal — Apollo te va a entender.",
                                 "en": "Ask your first question. You can write informally — Apollo will understand.",
                                 "pt": "Faça sua primeira pergunta. Pode escrever de forma informal — Apollo vai entender."},
    "emp.chat.input":          {"es": "Hacé una pregunta...",   "en": "Ask a question...",     "pt": "Faça uma pergunta..."},
    "emp.chat.processing":     {"es": "Apollo procesando → Atlas buscando...", "en": "Apollo processing → Atlas searching...", "pt": "Apollo processando → Atlas buscando..."},
    "emp.chat.escalated":      {"es": "Apollo detectó una señal de dificultad. Tu supervisor fue notificado.",
                                 "en": "Apollo detected a difficulty signal. Your supervisor has been notified.",
                                 "pt": "Apollo detectou um sinal de dificuldade. Seu supervisor foi notificado."},
    "emp.chat.quiz_enabled":   {"es": "Athena habilitó el quiz de Artemis para este módulo.",
                                 "en": "Athena enabled the Artemis quiz for this module.",
                                 "pt": "Athena ativou o quiz da Artemis para este módulo."},
    "emp.chat.quota":          {"es": "Apollo y Atlas alcanzaron el límite diario de consultas. Intentá de nuevo en unos minutos.",
                                 "en": "Apollo and Atlas reached today's query limit. Try again in a few minutes.",
                                 "pt": "Apollo e Atlas atingiram o limite diário de consultas. Tente novamente em alguns minutos."},
    "emp.chat.error":          {"es": "Hubo un problema procesando tu pregunta.",
                                 "en": "There was a problem processing your question.",
                                 "pt": "Ocorreu um problema ao processar sua pergunta."},
    "emp.progress":            {"es": "completado",             "en": "complete",              "pt": "concluído"},

    # ── Athena hardcoded responses ──
    "athena.greeting":     {"es": "¡Hola! Soy Atlas, tu asistente de onboarding. Podés preguntarme sobre políticas, procedimientos o cualquier duda del trabajo.",
                             "en": "Hi! I'm Atlas, your onboarding assistant. You can ask me about policies, procedures or any work-related question.",
                             "pt": "Olá! Sou Atlas, seu assistente de integração. Você pode me perguntar sobre políticas, procedimentos ou qualquer dúvida do trabalho."},
    "athena.out_of_domain":{"es": "Esa pregunta está fuera del alcance del sistema. Podés consultarme sobre políticas, procedimientos o cualquier tema de los documentos de la empresa.",
                             "en": "That question is outside the system's scope. You can ask me about policies, procedures or any topic from the company documents.",
                             "pt": "Essa pergunta está fora do escopo do sistema. Você pode me perguntar sobre políticas, procedimentos ou qualquer tema dos documentos da empresa."},
    "athena.module_done":  {"es": "Perfecto, registré que terminaste el módulo. Ahora Artemis va a generarte el quiz de comprensión.",
                             "en": "Great, I registered that you finished the module. Now Artemis will generate your comprehension quiz.",
                             "pt": "Ótimo, registrei que você concluiu o módulo. Agora Artemis vai gerar seu quiz de compreensão."},
    "athena.progress.title":{"es": "Tu progreso actual",            "en": "Your current progress",   "pt": "Seu progresso atual"},
    "athena.progress.module":{"es": "Módulo",                       "en": "Module",                  "pt": "Módulo"},
    "athena.progress.status.not_started":{"es":"No iniciado","en":"Not started","pt":"Não iniciado"},
    "athena.progress.status.in_progress":{"es":"En progreso","en":"In progress","pt":"Em andamento"},
    "athena.progress.status.completed":  {"es":"Completado","en":"Completed",  "pt":"Concluído"},
    "athena.progress.summary":{"es": "completado",                  "en": "complete",                "pt": "concluído"},
    "athena.progress.modules":{"es": "módulos",                     "en": "modules",                 "pt": "módulos"},

    # ── Alerts (Athena) ──
    "alert.stalled.msg":   {"es": "Sin avance por más de 3 días",
                             "en": "No progress for over 3 days",
                             "pt": "Sem progresso por mais de 3 dias"},
    "alert.stalled.act":   {"es": "Revisar si el empleado necesita apoyo adicional",
                             "en": "Check whether the employee needs additional support",
                             "pt": "Verifique se o funcionário precisa de apoio adicional"},
    "alert.breach.msg":    {"es": "Brecha detectada",
                             "en": "Breach detected",
                             "pt": "Lacuna detectada"},
    "alert.breach.act":    {"es": "Intervenir",
                             "en": "Intervene",
                             "pt": "Intervir"},

    # ── Atlas RAG fallbacks ──
    "atlas.no_docs":       {"es": "No encontré información sobre eso en los documentos cargados. Pedile al administrador que suba los documentos correspondientes, o consultá directamente con tu supervisor.",
                             "en": "I couldn't find information about that in the uploaded documents. Ask the administrator to upload the relevant documents, or consult your supervisor directly.",
                             "pt": "Não encontrei informações sobre isso nos documentos carregados. Peça ao administrador que envie os documentos relevantes, ou consulte diretamente seu supervisor."},
    "atlas.cant_generate": {"es": "No pude generar una respuesta clara con los documentos disponibles. Probá reformular la pregunta de otra manera.",
                             "en": "I couldn't generate a clear response with the available documents. Try rephrasing your question.",
                             "pt": "Não consegui gerar uma resposta clara com os documentos disponíveis. Tente reformular a pergunta."},
    "atlas.rate_limited":  {"es": "Estoy alcanzando el límite de consultas por minuto. Esperá un momento y volvé a preguntar.",
                             "en": "I'm hitting the per-minute query limit. Wait a moment and ask again.",
                             "pt": "Estou atingindo o limite de consultas por minuto. Espere um momento e tente novamente."},
    "atlas.error":         {"es": "Tuve un problema generando la respuesta. Probá reformular la pregunta.",
                             "en": "I had a problem generating the response. Try rephrasing your question.",
                             "pt": "Tive um problema gerando a resposta. Tente reformular a pergunta."},

    # ── Status / Common ──
    "status.completed":        {"es": "Completado",             "en": "Completed",             "pt": "Concluído"},
    "status.in_progress":      {"es": "En progreso",            "en": "In progress",           "pt": "Em andamento"},
    "status.not_started":      {"es": "No iniciado",            "en": "Not started",           "pt": "Não iniciado"},
    "status.verified":         {"es": "Verificado",             "en": "Verified",              "pt": "Verificado"},
    "status.not_verified":     {"es": "No verificado",          "en": "Not verified",          "pt": "Não verificado"},
    "status.breach":           {"es": "Brecha detectada",       "en": "Breach detected",       "pt": "Lacuna detectada"},
    "status.stalled":          {"es": "Estancado",              "en": "Stalled",               "pt": "Parado"},

    # ── Supervisor ──
    "sup.title":               {"es": "Panel del Supervisor",   "en": "Supervisor Dashboard",  "pt": "Painel do Supervisor"},
    "sup.subtitle":            {"es": "Alertas · Vista del equipo · Detalle por empleado",
                                 "en": "Alerts · Team Overview · Employee Detail",
                                 "pt": "Alertas · Visão da equipe · Detalhe por funcionário"},
    "sup.tab.alerts":          {"es": "Alertas",                "en": "Alerts",                "pt": "Alertas"},
    "sup.tab.overview":        {"es": "Vista del equipo",       "en": "Team Overview",         "pt": "Visão da equipe"},
    "sup.tab.detail":          {"es": "Detalle por empleado",   "en": "Employee Detail",       "pt": "Detalhe do funcionário"},
    "sup.tab.docs":            {"es": "Documentos",             "en": "Documents",             "pt": "Documentos"},
    "sup.docs.title":          {"es": "Documentación oficial",  "en": "Official documentation","pt": "Documentação oficial"},
    "sup.docs.desc":           {"es": "Documentos oficiales cargados por el administrador. Son la fuente de la que el sistema genera las rutas y fundamenta las respuestas.",
                                 "en": "Official documents uploaded by the administrator. They are the source the system uses to generate routes and ground answers.",
                                 "pt": "Documentos oficiais enviados pelo administrador. São a fonte que o sistema usa para gerar trajetos e fundamentar respostas."},
    "sup.docs.empty":          {"es": "No hay documentos cargados todavía.", "en": "No documents uploaded yet.", "pt": "Nenhum documento enviado ainda."},
    "sup.detail.answer":       {"es": "Respuesta del empleado", "en": "Employee's answer",     "pt": "Resposta do funcionário"},

    # ── Captura de conocimiento (Chiron) ──
    "sup.tab.capture":         {"es": "Enseñar a Mythos",       "en": "Teach Mythos",          "pt": "Ensinar ao Mythos"},
    "sup.capture.title":       {"es": "Captura de conocimiento — Chiron", "en": "Knowledge capture — Chiron", "pt": "Captura de conhecimento — Chiron"},
    "sup.capture.intro":       {"es": "¿No tenés tiempo de explicar lo mismo una y otra vez? Enseñale a Mythos una sola vez. Chiron te hace preguntas guiadas, convierte tus respuestas en documentación y la deja disponible para que el asistente responda a los empleados por vos.",
                                 "en": "No time to explain the same thing over and over? Teach Mythos once. Chiron asks you guided questions, turns your answers into documentation and makes it available so the assistant answers employees for you.",
                                 "pt": "Sem tempo para explicar a mesma coisa repetidamente? Ensine ao Mythos uma vez. Chiron faz perguntas guiadas, transforma suas respostas em documentação e a disponibiliza para que o assistente responda aos funcionários por você."},
    "sup.capture.topic_label": {"es": "¿Qué puesto o tema querés documentar?", "en": "Which role or topic do you want to document?", "pt": "Qual cargo ou tema você quer documentar?"},
    "sup.capture.topic_ph":    {"es": "Ej: Atención de tickets de soporte nivel 1", "en": "E.g.: Level 1 support ticket handling", "pt": "Ex: Atendimento de tickets de suporte nível 1"},
    "sup.capture.generate":    {"es": "Generar preguntas guiadas", "en": "Generate guided questions", "pt": "Gerar perguntas guiadas"},
    "sup.capture.generating":  {"es": "Chiron preparando preguntas...", "en": "Chiron preparing questions...", "pt": "Chiron preparando perguntas..."},
    "sup.capture.need_topic":  {"es": "Escribí primero el puesto o tema a documentar.", "en": "Write the role or topic to document first.", "pt": "Escreva primeiro o cargo ou tema a documentar."},
    "sup.capture.answer_label":{"es": "Tu respuesta",           "en": "Your answer",           "pt": "Sua resposta"},
    "sup.capture.answers_hint":{"es": "Respondé con tus palabras. No hace falta completar todas: Chiron usa lo que escribas.",
                                 "en": "Answer in your own words. You don't need to fill them all: Chiron uses whatever you write.",
                                 "pt": "Responda com suas palavras. Não precisa preencher todas: Chiron usa o que você escrever."},
    "sup.capture.save":        {"es": "Enseñar a Mythos",       "en": "Teach Mythos",          "pt": "Ensinar ao Mythos"},
    "sup.capture.saving":      {"es": "Chiron documentando e indexando...", "en": "Chiron documenting and indexing...", "pt": "Chiron documentando e indexando..."},
    "sup.capture.empty":       {"es": "Completá al menos una respuesta antes de enseñar.", "en": "Fill at least one answer before teaching.", "pt": "Preencha pelo menos uma resposta antes de ensinar."},
    "sup.capture.saved":       {"es": "Mythos aprendió. Conocimiento documentado e indexado:", "en": "Mythos learned. Knowledge documented and indexed:", "pt": "Mythos aprendeu. Conhecimento documentado e indexado:"},
    "sup.capture.fragments":   {"es": "fragmentos. Ya está disponible en el asistente y para las rutas.", "en": "fragments. It's now available in the assistant and for routes.", "pt": "fragmentos. Já está disponível no assistente e para os trajetos."},
    "sup.capture.preview":     {"es": "Ver documento generado", "en": "View generated document", "pt": "Ver documento gerado"},
    "sup.capture.new":         {"es": "Documentar otro tema",   "en": "Document another topic", "pt": "Documentar outro tema"},
    "sup.capture.error":       {"es": "Chiron tuvo un problema. Reintentá en un momento.", "en": "Chiron had a problem. Retry in a moment.", "pt": "Chiron teve um problema. Tente novamente em instantes."},
    "sup.capture.quota":       {"es": "Chiron alcanzó el límite de consultas. Esperá unos minutos.", "en": "Chiron reached the query limit. Wait a few minutes.", "pt": "Chiron atingiu o limite de consultas. Aguarde alguns minutos."},
    "sup.alerts.title":        {"es": "Alertas activas",        "en": "Active Alerts",         "pt": "Alertas ativos"},
    "sup.alerts.desc":         {"es": "Athena monitorea brechas detectadas y empleados sin avance por más de 3 días.",
                                 "en": "Athena monitors detected breaches and employees with no progress for over 3 days.",
                                 "pt": "Athena monitora lacunas detectadas e funcionários sem progresso por mais de 3 dias."},
    "sup.alerts.none":         {"es": "Sin alertas activas. Todos los empleados están avanzando con normalidad.",
                                 "en": "No active alerts. All employees are progressing normally.",
                                 "pt": "Sem alertas ativos. Todos os funcionários estão progredindo normalmente."},
    "sup.alerts.action":       {"es": "Acción sugerida",        "en": "Suggested action",      "pt": "Ação sugerida"},
    "sup.team.title":          {"es": "Progreso del equipo",    "en": "Team Progress",         "pt": "Progresso da equipe"},
    "sup.team.refresh":        {"es": "Actualizar",             "en": "Refresh",               "pt": "Atualizar"},
    "sup.team.loading":        {"es": "Artemis cargando datos del equipo...", "en": "Artemis loading team data...", "pt": "Artemis carregando dados da equipe..."},
    "sup.team.empty":          {"es": "Sin empleados registrados aún.", "en": "No employees registered yet.", "pt": "Nenhum funcionário cadastrado ainda."},
    "sup.team.with_breach":    {"es": "empleado(s) con brecha detectada por Artemis",
                                 "en": "employee(s) with breach detected by Artemis",
                                 "pt": "funcionário(s) com lacuna detectada por Artemis"},
    "sup.team.complete":       {"es": "completado",             "en": "complete",              "pt": "concluído"},
    "sup.team.progress":       {"es": "Progreso",               "en": "Progress",              "pt": "Progresso"},
    "sup.detail.empty":        {"es": "Sin empleados registrados.", "en": "No employees registered.", "pt": "Nenhum funcionário cadastrado."},
    "sup.detail.employee":     {"es": "Empleado",               "en": "Employee",              "pt": "Funcionário"},
    "sup.detail.status":       {"es": "Estado",                 "en": "Status",                "pt": "Estado"},
    "sup.detail.time":         {"es": "Tiempo dedicado",        "en": "Time spent",            "pt": "Tempo dedicado"},
    "sup.detail.quiz_detail":  {"es": "Detalle del quiz — calificado por Artemis",
                                 "en": "Quiz detail — graded by Artemis",
                                 "pt": "Detalhe do quiz — corrigido por Artemis"},
    "sup.detail.diagnosis":    {"es": "Diagnóstico de Artemis", "en": "Artemis Diagnosis",     "pt": "Diagnóstico de Artemis"},
    "sup.detail.suggested":    {"es": "Acción sugerida",        "en": "Suggested action",      "pt": "Ação sugerida"},
    "sup.detail.analyze":      {"es": "Analizar con Artemis",   "en": "Analyze with Artemis",  "pt": "Analisar com Artemis"},
    "sup.detail.analyzing":    {"es": "Artemis analizando...",  "en": "Artemis analyzing...",  "pt": "Artemis analisando..."},
    "sup.detail.not_started":  {"es": "Módulo no iniciado todavía.", "en": "Module not started yet.", "pt": "Módulo ainda não iniciado."},
    "sup.detail.chat_history": {"es": "Historial de chat",      "en": "Chat history",          "pt": "Histórico de chat"},
    "sup.detail.messages":     {"es": "mensajes",               "en": "messages",              "pt": "mensagens"},
    "sup.detail.sender_emp":   {"es": "Empleado",               "en": "Employee",              "pt": "Funcionário"},

    # ── Roles ──
    "role.admin":      {"es": "Administrador", "en": "Administrator", "pt": "Administrador"},
    "role.supervisor": {"es": "Supervisor",    "en": "Supervisor",    "pt": "Supervisor"},
    "role.employee":   {"es": "Empleado",      "en": "Employee",      "pt": "Funcionário"},

    # ── Errors ──
    "err.app_no_role":    {"es": "Rol no reconocido", "en": "Unrecognized role", "pt": "Função não reconhecida"},
    "err.app_no_company": {"es": "Tu cuenta no tiene empresa asignada. Contactá al administrador.",
                            "en": "Your account has no company assigned. Contact the administrator.",
                            "pt": "Sua conta não tem empresa atribuída. Entre em contato com o administrador."},
}


def init_lang():
    if "lang" not in st.session_state:
        st.session_state.lang = DEFAULT_LANG


def get_lang() -> str:
    return st.session_state.get("lang", DEFAULT_LANG)


def set_lang(lang: str):
    if lang in LANGS:
        st.session_state.lang = lang


def t(key: str) -> str:
    lang = get_lang()
    entry = T.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get(DEFAULT_LANG) or key


def t_lang(key: str, lang: str) -> str:
    """Versión sin Streamlit context — para agentes que reciben lang explícito."""
    entry = T.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get(DEFAULT_LANG) or key


def lang_name(lang: str) -> str:
    """Nombre del idioma para inyectar en prompts de LLM."""
    return {"es": "español", "en": "English", "pt": "português brasileño"}.get(lang, "español")


def selector():
    """Dropdown de idioma arriba a la derecha."""
    init_lang()
    cur = get_lang()
    cols = st.columns([10, 1.6])
    with cols[1]:
        choice = st.selectbox(
            "lang",
            LANGS,
            index=LANGS.index(cur),
            format_func=lambda c: f"  {c.upper()}   {LANG_LABELS[c]}",
            label_visibility="collapsed",
            key="lang_selector_box",
        )
        if choice != cur:
            set_lang(choice)
            st.rerun()
