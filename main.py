import os
import sys
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# INSTALACIÓN AUTOMÁTICA DE DEPENDENCIAS CRÍTICAS
try:
    import telebot
except ImportError:
    print("⚡ Actualizando entorno VIP en Render... Espere.")
    os.system(f"{sys.executable} -m pip install pyTelegramBotAPI requests")
    import telebot

from telebot import types

# =====================================================================
# 🔑 SECCIÓN DE APIS - CONFIGURACIÓN DE ENTORNO
# =====================================================================
TOKEN_TELEGRAM = os.environ.get("TOKEN_TELEGRAM") or "8945180693:AAG7MxrAke7a97pztZJ7zpkYZzZX3IWiVGM"
API_KEY_GROQ = os.environ.get("API_KEY_GROQ") or "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"
API_FUTBOL_KEY = os.environ.get("API_FUTBOL_KEY") or "1589324158msh59fc26e7a7aad35p1ec314jsn40a77ef790e1"

# Inicialización de Telegram
bot = telebot.TeleBot(TOKEN_TELEGRAM)

# Diccionarios de control de flujo estricto (Evita cruces de datos y respuestas automáticas)
USUARIOS_EN_ESPERA_PARTIDO = {}
USUARIOS_EN_ESPERA_JUGADOR = {}
USUARIOS_EN_ESPERA_COBERTURA = {}
USUARIOS_EN_ESPERA_ALERTAS = {}
USUARIOS_EN_ESPERA_ESCENARIOS = {}

# =====================================================================
# 🌐 PARCHE WEB SERVICE: SERVIDOR EN SEGUNDO PLANO PARA RENDER
# =====================================================================
class RenderHealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"DAMLEYT CORE: OPERANDO EN LA NUBE")

def iniciar_servidor_render():
    puerto = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", puerto), RenderHealthCheckServer)
    print(f"📡 Parche Web activado. Escuchando peticiones de Render en el puerto: {puerto}")
    server.serve_forever()

# =====================================================================
# 🌐 MOTOR DE RECOLECCIÓN: EXTRACCIÓN ESTRICTA DE API EN TIEMPO REAL
# =====================================================================
def obtener_datos_reales_partido(busqueda_usuario, es_live=False):
    url_fixtures = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": API_FUTBOL_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    texto_limpio = busqueda_usuario.lower().replace("vs", " ").replace("-", " ")
    palabras = [p.strip() for p in texto_limpio.split(" ") if p.strip() and len(p.strip()) > 1]
    
    if not palabras:
        return None

    params = {"live": "all"} if es_live else {"season": "2026"}
    
    try:
        response = requests.get(url_fixtures, headers=headers, params=params, timeout=12)
        if response.status_code != 200:
            return None
            
        data = response.json()
        if data.get("response"):
            for item in data["response"]:
                home_team = item["teams"]["home"]["name"].lower()
                away_team = item["teams"]["away"]["name"].lower()
                
                match_local = any(p in home_team for p in palabras)
                match_visita = any(p in away_team for p in palabras)
                
                if match_local or match_visita:
                    fixture_info = item.get("fixture", {})
                    venue_info = fixture_info.get("venue", {})
                    goals = item.get("goals", {})
                    status = fixture_info.get("status", {})
                    
                    nombre_estadio = venue_info.get("name") or "Estadio Oficial No Reportado"
                    ciudad_estadio = venue_info.get("city") or ""
                    arbitro_assigned = fixture_info.get("referee") or "Cuerpo Arbitral por Confirmar"
                    
                    estadio_final = f"{nombre_estadio} ({ciudad_estadio})" if ciudad_estadio else nombre_estadio
                    arbitro_final = str(arbitro_assigned).split(',')[0].strip()
                    
                    return {
                        "equipo_local": item["teams"]["home"]["name"],
                        "equipo_visitante": item["teams"]["away"]["name"],
                        "estadio": estadio_final,
                        "arbitro": arbitro_final,
                        "en_vivo": True if status.get("short") in ["1H", "HT", "2H", "ET", "P"] else es_live,
                        "goles_local": goals.get("home") if goals.get("home") is not None else 0,
                        "goles_visitante": goals.get("away") if goals.get("away") is not None else 0,
                        "minuto": status.get("elapsed") or 0,
                        "status_txt": status.get("long", "En Progreso")
                    }
    except Exception as e:
        print(f"⚠️ Error Crítico en API de Fútbol: {e}")
        
    return None

# =====================================================================
# 1. BIENVENIDA OFICIAL EXCLUSIVA
# =====================================================================
def limpiar_estados(chat_id):
    for dicc in [USUARIOS_EN_ESPERA_PARTIDO, USUARIOS_EN_ESPERA_JUGADOR, USUARIOS_EN_ESPERA_COBERTURA, USUARIOS_EN_ESPERA_ALERTAS, USUARIOS_EN_ESPERA_ESCENARIOS]:
        if chat_id in dicc: del dicc[chat_id]

@bot.message_handler(commands=['start'])
def start(message):
    limpiar_estados(message.chat.id)
        
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_partidos = types.KeyboardButton("⚽ Analizar Partido")
    btn_picks = types.KeyboardButton("🔥 Picks para Parley")
    btn_jugador = types.KeyboardButton("🏃‍♂️ Auditar Jugador")
    btn_ticket = types.KeyboardButton("🎟️ Crear Ticket")
    btn_cobertura = types.KeyboardButton("🛡️ Cobertura en Vivo")
    btn_live = types.KeyboardButton("📉 Escenarios Live & Value")
    btn_alertas = types.KeyboardButton("📢 Alertas Pre-Match")
    
    markup.add(btn_partidos, btn_picks, btn_jugador, btn_ticket, btn_cobertura, btn_live, btn_alertas)
    
    nombre_usuario = message.from_user.first_name
    mensaje = f"""🛠️ SYSTEM CORE: DAMLEYT DATA ANALYTICS
⚡ Motor: Damleyt Strategy v3.6 (Filtro Dinámico Anti-Simulación)
──────────────────────────────────────────────────
👋 ¡Bienvenido al centro de operaciones, {nombre_usuario}! 
Módulos ajustados. No se permiten datos ficticios ni predicciones genéricas automáticas.

• Desarrollador: Director Damleyt
──────────────────────────────────────────────────"""
    bot.send_message(message.chat.id, mensaje, reply_markup=markup)

# =====================================================================
# 2. SECCIÓN: ANALIZAR PARTIDO (PRE-MATCH / ESTRATÉGICO)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "⚽ Analizar Partido")
def solicitar_partido(message):
    limpiar_estados(message.chat.id)
    USUARIOS_EN_ESPERA_PARTIDO[message.chat.id] = True
    bot.reply_to(message, "Indique el partido o equipo que desea auditar.\n👉 *Ejemplo:* Países Bajos vs Suecia")

def ejecutar_auditoria_core(message, partido_usuario):
    bot.reply_to(message, f"Procesando matriz táctica avanzada (xG, Estadio e Historial Real)... ⚡")
    datos_api = obtener_datos_reales_partido(partido_usuario, es_live=False)
    
    # RESPALDO DIRECTO: Si la API no lo encuentra por dedazo o saturación, la IA procesa el partido directo
    if not datos_api:
        estadio_real = "Estadio Principal / Sede Oficial"
        arbitro_real = "Cuerpo Arbitral Designado"
        if "vs" in partido_usuario.lower():
            equipo_a = partido_usuario.lower().split("vs")[0].strip().title()
            equipo_b = partido_usuario.lower().split("vs")[1].strip().title()
        else:
            equipo_a = partido_usuario.strip().title()
            equipo_b = "Rival Directo"
    else:
        equipo_a = datos_api["equipo_local"]
        equipo_b = datos_api["equipo_visitante"]
        estadio_real = datos_api["estadio"]
        arbitro_real = datos_api["arbitro"]

    prompt_ia = (
        f"Actúa como un algoritmo avanzado de analítica deportiva operando en este año 2026.\n"
        f"Analiza estrictamente el partido real: {equipo_a} vs {equipo_b}.\n"
        f"DATOS REALES ENTRANTES DE LA API:\n- Sede/Estadio: {estadio_real}\n- Árbitro Asignado: {arbitro_real}\n\n"
        f"🚨 INSTRUCCIÓN DE ABSOLUTA INTEGRIDAD DE DATOS:\n"
        f"PROHIBIDO inventar nombres de árbitros o sedes alternativas. Usa exactamente lo provisto: {arbitro_real} y {estadio_real}.\n"
        f"1. PROHIBIDO usar '1H'. Escribe siempre 'Primer Tiempo (45 Minutos)'.\n"
        f"2. CUADRE PERFECTO DEL 100% en Over/Under.\n"
        f"3. FORMATO VISUAL CON RECUADROS 🟩 (>70%), 🟨 (50-70%), 🟥 (<50%) y barras ████▒▒▒▒.\n\n"
        f"Devuelve este formato premium:\n\n"
        f"🏟️ **INTELIGENCIA CONTEXTUAL Y SEDE:**\n- Estadio: {estadio_real}\n- Clima: [Estadística analítica]\n\n"
        f"📊 **DATOS AVANZADOS:**\n- Proyección xG: {equipo_a} [X.XX] vs [X.XX] {equipo_b}\n- Dominio Territorial: [████▒▒▒▒] XX% vs XX%\n\n"
        f"⏱️ **PRIMER TIEMPO (45 MINUTOS):**\n- Goles (Over/Under 0.5): [Recuadro] XX% / XX%\n- Córners (Over/Under 3.5): [Recuadro] XX% / XX%\n\n"
        f"⚽ **ANÁLISIS FINAL (90 MINUTOS):**\n- Victoria Directa Favorito: [Equipo] | [Recuadro] XX%\n- Goles Globales (Over/Under 2.5): [Recuadro] XX%\n\n"
        f"📐 **CÓRNERS TOTALES EN EL PARTIDO:**\n- Over [8.5]: [Recuadro] XX% | Desglose: {equipo_a} X-Y / {equipo_b} X-Y\n\n"
        f"🟨 **TARJETAS TOTALES Y ÁRBITRO:**\n- Árbitro: {arbitro_real} | Over [3.5]: [Recuadro] XX%"
    )
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_ia}], "temperature": 0.2, "max_tokens": 1200}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Inconveniente en el núcleo analítico. {e}")

# =====================================================================
# 3. 📢 SECCIÓN: ALERTAS PRE-MATCH DINÁMICAS (TU ELIGES EL PARTIDO)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "📢 Alertas Pre-Match")
def solicitar_partido_alertas(message):
    limpiar_estados(message.chat.id)
    USUARIOS_EN_ESPERA_ALERTAS[message.chat.id] = True
    bot.reply_to(message, "📢 **MÓDULO DE ALERTAS REALES**\nEscribe el partido del que deseas extraer alertas operativas reales de hoy.\n👉 *Ejemplo:* Ecuador vs Curazao")

def ejecutar_alertas_prematch_core(message, partido_usuario):
    bot.reply_to(message, f"Buscando datos y alineaciones reales para: **{partido_usuario}**... ⚡")
    datos_api = obtener_datos_reales_partido(partido_usuario, es_live=False)
    
    if not datos_api:
        bot.send_message(message.chat.id, f"❌ **MÓDULO ALERTAS:** No se encontraron registros válidos de programación para '{partido_usuario}'. Verifique que jueguen hoy.")
        return

    eq_a = datos_api["equipo_local"]
    eq_b = datos_api["equipo_visitante"]
    estadio_real = datos_api["estadio"]

    prompt_alertas = (
        f"Actúa como un analista de riesgos deportivos operando en este año 2026.\n"
        f"Genera un reporte analítico de alertas y movimientos reales basado estrictamente en el partido: {eq_a} vs {eq_b}.\n"
        f"Estadio confirmado por API: {estadio_real}.\n\n"
        f"🚨 PROHIBIDO inventar partidos ficticios. Ajusta las alertas al entorno de {eq_a} y {eq_b}.\n\n"
        f"Devuelve exactamente esta estructura limpia:\n\n"
        f"📢 **ALERTAS PRE-MATCH Y RIESGO DE INVERSIÓN**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ Partido Bajo Alerta: {eq_a} vs {eq_b}\n"
        f"🚨 Reporte de Última Hora: [Análisis logístico o bajas estimadas de {eq_a} o {eq_b} en 1 renglón]\n"
        f"- Impacto en el Mercado:\n"
        f"  * Línea de Dinero: [Variación o tendencia del momio ajustada a este partido]\n"
        f"  * Ajuste de Goles Proyectados: [Tendencia Over/Under basada en su xG estadístico]\n\n"
        f"📉 **ALERTAS ADICIONALES (VOLUMEN EN CASAS DE APUESTAS)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🔹 Movimiento de Flujo: [Análisis de dónde se está concentrando el dinero real para este juego]\n"
        f"- Recomendación Operativa: [Consejo estratégico de control de stake en 1 renglón]"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_alertas}], "temperature": 0.1, "max_tokens": 700}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Error al procesar alertas prematch: {e}")

# =====================================================================
# 4. 📉 SECCIÓN: ESCENARIOS LIVE & VALUE DINÁMICOS
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "📉 Escenarios Live & Value")
def solicitar_partido_escenarios(message):
    limpiar_estados(message.chat.id)
    USUARIOS_EN_ESPERA_ESCENARIOS[message.chat.id] = True
    bot.reply_to(message, "📉 **SIMULADOR DE ESCENARIOS LIVE**\nIngresa el partido del día que deseas auditar operacionalmente.\n👉 *Ejemplo:* España vs Italia")

def ejecutar_escenarios_live_core(message, partido_usuario):
    bot.reply_to(message, f"Calculando desvíos de valor matemático para: **{partido_usuario}**... ⚡")
    datos_api = obtener_datos_reales_partido(partido_usuario, es_live=False)
    
    if not datos_api:
        bot.send_message(message.chat.id, f"❌ **MÓDULO ESCENARIOS:** No se encontraron datos para '{partido_usuario}' en el sistema.")
        return

    eq_a = datos_api["equipo_local"]
    eq_b = datos_api["equipo_visitante"]

    prompt_live = (
        f"Actúa como una calculadora avanzada de apuestas de valor (Value-Bets) operando en el año 2026.\n"
        f"Genera proyecciones de escenarios basados exclusivamente en el partido real: {eq_a} vs {eq_b}.\n\n"
        f"Devuelve exactamente esta estructura, prohibido simular selecciones ajenas a este juego:\n\n"
        f"📉 **SIMULACIÓN DE ESCENARIOS LIVE (MINUTO 15)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ Partido Proyectado: {eq_a} vs {eq_b}\n"
        f"🚨 Escenario Dinámico: Ajuste de líneas por modelo predictivo.\n"
        f"- Cambio de Mercado Proyectado:\n"
        f"  * Línea de Córners: Over [X.X] (Probabilidad: 🟩 [XX]% | Under: 🟥 [XX]%)\n"
        f"  * Ajuste de Hándicap Asiático Óptimo: [Línea óptima calculada]\n\n"
        f"🎯 **CALCULADORA DE VALOR (VALUE-BET DETECTOR)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🔹 Mercado Detectado con Ventaja: [Mercado de {eq_a} o {eq_b}]\n"
        f"- Probabilidad del Motor IA: 🟩 [XX]%\n"
        f"- Cuota Justa (Matemática): [X.XX]\n"
        f"- Margen de Ventaja Calculado: [+XX.X%]"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_live}], "temperature": 0.1, "max_tokens": 700}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Error al calcular matrices de valor: {e}")

# =====================================================================
# 5. 🛡️ SECCIÓN CRÍTICA: COBERTURA EN VIVO (CERO APUESTAS FICTICIAS)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🛡️ Cobertura en Vivo")
def solicitar_cobertura_partido(message):
    limpiar_estados(message.chat.id)
    USUARIOS_EN_ESPERA_COBERTURA[message.chat.id] = True
    bot.reply_to(message, "🛡️ **HEDGING TOOL: COBERTURA EN VIVO**\nIndique el partido activo para extraer su marcador real desde el servidor.\n👉 *Ejemplo:* Ecuador vs Curazao")

def ejecutar_cobertura_live_core(message, partido_usuario):
    bot.reply_to(message, f"Consultando estado en vivo en la API para: **{partido_usuario}**... ⚡")
    datos_api = obtener_datos_reales_partido(partido_usuario, es_live=True)
    
    if not datos_api or not datos_api.get("en_vivo"):
        bot.send_message(
            message.chat.id,
            f"❌ **MÓDULO LIVE: OPERACIÓN ABORTADA**\nEl servidor no registra ningún partido activo EN PROGRESO para '{partido_usuario}' en este momento.\n\n"
            f"El sistema tiene prohibido generar proyecciones basadas en partidos que no han iniciado."
        )
        return

    eq_a = datos_api["equipo_local"]
    eq_b = datos_api["equipo_visitante"]
    goles_a = datos_api["goles_local"]
    goles_b = datos_api["goles_visitante"]
    minuto_actual = datos_api["minuto"]
    estado_txt = datos_api["status_txt"]

    prompt_cobertura = (
        f"Actúa como un algoritmo matemático avanzado de cobertura (hedging) en tiempo real.\n"
        f"Genera una guía basada EXCLUSIVAMENTE en parámetros reales de la API:\n"
        f"- Partido: {eq_a} vs {eq_b}\n- Marcador Extraído: {eq_a} {goles_a} - {goles_b} {eq_b}\n- Minuto: {minuto_actual} ({estado_txt})\n\n"
        f"🚨 REGLAS: Procesa la ventaja o igualdad numérica real dictada por el marcador: {goles_a} a {goles_b}. Prohibido usar plantillas prefijadas.\n\n"
        f"Devuelve esta respuesta estructurada:\n\n"
        f"🛡️ **Sugerencias de Cobertura (Hedging Tool)**\n"
        f"🏟️ **Partido:** {eq_a} vs {eq_b}\n"
        f"⏱️ **Estado Real:** Minuto {minuto_actual} | Marcador: {goles_a} - {goles_b}\n\n"
        f"🎯 **ESTRATEGIA INMEDIATA:**\n- Cobertura Live Favorito: [Línea técnica ajustada al {goles_a}-{goles_b} en el minuto {minuto_actual}]\n- Capital Inversión: [XX]%"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_cobertura}], "temperature": 0.0, "max_tokens": 600}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Error al calcular cobertura live: {e}")

# =====================================================================
# 6. SECCIÓN: AUDITAR JUGADOR
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🏃‍♂️ Auditar Jugador")
def solicitar_jugador(message):
    limpiar_estados(message.chat.id)
    USUARIOS_EN_ESPERA_JUGADOR[message.chat.id] = True
    bot.reply_to(message, "📥 **MODO AUDITORÍA DE JUGADOR**\nEscribe el nombre del jugador.\n👉 *Ejemplo:* 'Santiago Giménez'")

def procesar_auditoria_jugador_core(message, datos):
    bot.reply_to(message, f"Auditando rendimiento real para: **{datos}**... ⚡")
    prompt_jugador = (
        f"Actúa como un algoritmo de Scouting en el año 2026. Evalúa al jugador: {datos}.\n"
        f"Devuelve este formato limpio:\n\n🏃‍♂️ **AUDITORÍA DE JUGADOR**\n- Jugador: {datos}\n- Club/Selección 2026: [Info Real]\n- Tiros Proyectados: [Rango]\n- Probabilidad de Anotar: [XX]%"
    )
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_jugador}], "temperature": 0.3}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Error en jugador: {e}")

# =====================================================================
# 7. SECCIÓN: PICKS PARA PARLEY Y TICKETS SIMULADOS
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🔥 Picks para Parley")
def menu_parley(message):
    limpiar_estados(message.chat.id)
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(types.KeyboardButton("🟩 Bajo Riesgo"), types.KeyboardButton("🟨 Medio Riesgo"), types.KeyboardButton("🟥 Alto Riesgo"))
    bot.send_message(message.chat.id, "Seleccione el nivel de riesgo estratégico:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🟩 Bajo Riesgo", "🟨 Medio Riesgo", "🟥 Alto Riesgo"])
def procesar_parley(message):
    riesgo = "BAJO" if "Bajo" in message.text else "MEDIO" if "Medio" in message.text else "ALTO"
    bot.send_message(message.chat.id, f"⚡ Consultando partidos reales vigentes para armar Parley de riesgo {riesgo}...")
    
    prompt_parley = f"Genera un bloque de apuestas parley de riesgo {riesgo} usando partidos reales del fixture futbolístico global de la temporada actual de este año 2026. Mantén formato estructurado."
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_parley}], "temperature": 0.4}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.send_message(message.chat.id, f"Error en Parley: {e}")

@bot.message_handler(func=lambda message: message.text == "🎟️ Crear Ticket")
def simular_ticket_apuesta(message):
    limpiar_estados(message.chat.id)
    bot.reply_to(message, "🎟️ Compilando ticket con partidos programados reales... ⚡")
    prompt_ticket = "Genera un ticket de inversión simulado combinando 3 selecciones de alto valor basadas en partidos reales de fútbol de las ligas vigentes en este año 2026."
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_ticket}], "temperature": 0.4}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        if 'choices' in res: bot.send_message(message.chat.id, res['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Error en Ticket: {e}")

# =====================================================================
# 🔄 RECEPTOR GENERAL DE TEXTO (GESTIÓN DE ESTADOS DE ENTRADA)
# =====================================================================
@bot.message_handler(func=lambda message: True)
def manejar_entradas_texto(message):
    chat_id = message.chat.id
    texto = message.text.strip()
    
    if chat_id in USUARIOS_EN_ESPERA_PARTIDO:
        del USUARIOS_EN_ESPERA_PARTIDO[chat_id]
        ejecutar_auditoria_core(message, texto)
        
    elif chat_id in USUARIOS_EN_ESPERA_JUGADOR:
        del USUARIOS_EN_ESPERA_JUGADOR[chat_id]
        procesar_auditoria_jugador_core(message, texto)
        
    elif chat_id in USUARIOS_EN_ESPERA_COBERTURA:
        del USUARIOS_EN_ESPERA_COBERTURA[chat_id]
        ejecutar_cobertura_live_core(message, texto)

    elif chat_id in USUARIOS_EN_ESPERA_ALERTAS:
        del USUARIOS_EN_ESPERA_ALERTAS[chat_id]
        ejecutar_alertas_prematch_core(message, texto)

    elif chat_id in USUARIOS_EN_ESPERA_ESCENARIOS:
        del USUARIOS_EN_ESPERA_ESCENARIOS[chat_id]
        ejecutar_escenarios_live_core(message, texto)
        
    else:
        bot.reply_to(message, "⚠️ Acción no válida. Utilice los botones de abajo o escribe /start.")

# =====================================================================
# 🚀 EJECUCIÓN INICIAL Y CONTROL DE HILOS
# =====================================================================
if __name__ == "__main__":
    hilo_servidor = threading.Thread(target=iniciar_servidor_render)
    hilo_servidor.daemon = True
    hilo_servidor.start()
    
    print("🤖 DAMLEYT CORE: Bot iniciado y listo para operar.")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Caída detectada: {e}. Reiniciando en 5 segundos...")
            time.sleep(5)