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

# Diccionarios de control de flujo estricto (Evita cruces de datos)
USUARIOS_EN_ESPERA_PARTIDO = {}
USUARIOS_EN_ESPERA_JUGADOR = {}
USUARIOS_EN_ESPERA_COBERTURA = {}

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

    # Parámetros estrictos: Live filtra solo partidos activos, sino busca en la temporada 2026
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
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
        
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
⚡ Motor: Damleyt Strategy v3.5 (Suite de Inteligencia Completa)
──────────────────────────────────────────────────
👋 ¡Bienvenido al centro de operaciones, {nombre_usuario}! 
Se han cargado los 15 módulos analíticos de alta gama (Estadísticas xG, Bloques Tácticos, Posesión Efectiva, Altitud e Interfaz Avanzada).

• Desarrollador: Director Damleyt
──────────────────────────────────────────────────"""
    bot.send_message(message.chat.id, mensaje, reply_markup=markup)

# =====================================================================
# 2. SECCIÓN: ANALIZAR PARTIDO (PRE-MATCH / ESTRATÉGICO)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "⚽ Analizar Partido")
def solicitar_partido(message):
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    USUARIOS_EN_ESPERA_PARTIDO[message.chat.id] = True
    bot.reply_to(
        message, 
        "Indique el partido o equipo que desea auditar.\n"
        "👉 *Ejemplo:* Países Bajos vs Suecia"
    )

def ejecutar_auditoria_core(message, partido_usuario):
    bot.reply_to(message, f"Procesando matriz táctica avanzada (xG, Presión Atmosférica, Fatiga e Historial Ponderado)... ⚡")
    
    datos_api = obtener_datos_reales_partido(partido_usuario, es_live=False)
    
    if not datos_api:
        bot.send_message(
            message.chat.id,
            f"❌ **ERROR DE AUDITORÍA:** No se encontraron registros de programación ni datos válidos para '{partido_usuario}' en la API de Fútbol para la temporada actual. Verifique el nombre e intente de nuevo."
        )
        return
    
    equipo_a = datos_api["equipo_local"]
    equipo_b = datos_api["equipo_visitante"]
    estadio_real = datos_api["estadio"]
    arbitro_real = datos_api["arbitro"]

    prompt_ia = (
        f"Actúa como un algoritmo avanzado de analítica deportiva operando en este año 2026.\n"
        f"Analiza estrictamente el partido: {equipo_a} vs {equipo_b}.\n"
        f"DATOS REALES ENTRANTES DE LA API:\n"
        f"- Sede/Estadio: {estadio_real}\n"
        f"- Árbitro Asignado: {arbitro_real}\n\n"
        f"🚨 INSTRUCCIÓN DE ABSOLUTA INTEGRIDAD DE DATOS:\n"
        f"PROHIBIDO inventar nombres de árbitros o sedes alternativas. Usa exactamente lo provisto: {arbitro_real} y {estadio_real}.\n"
        f"El mercado de 'Primer Tiempo (45 Minutos)' y los 'Córners Totales' deben fluctuar libremente reflejando tendencias analíticas coherentes.\n\n"
        f"🚨 FILTRO REGENERATIVO OBLIGATORIO 2026:\n"
        f"Prohibido basar análisis o mencionar futbolistas fuera del proceso actual de este año 2026.\n\n"
        f"REGLAS OBLIGATORIAS DE DISEÑO:\n"
        f"1. PROHIBIDO usar '1H'. Escribe siempre 'Primer Tiempo (45 Minutos)'.\n"
        f"2. CUADRE PERFECTO DEL 100%: En los mercados Over/Under muestra ambos porcentajes y la suma debe dar exactamente 100%.\n"
        f"3. FORMATO VISUAL CON RECUADROS OBLIGATORIOS Y GRÁFICOS DE BARRAS DE TEXTO:\n"
        f"   - Si la opción tiene >70%: Pon el recuadro verde 🟩 seguido del porcentaje.\n"
        f"   - Si la opción tiene entre 50% y 70%: Pon el recuadro amarillo 🟨 seguido del porcentaje.\n"
        f"   - Si la opción tiene <50%: Pon el recuadro rojo 🟥 seguido del porcentaje.\n"
        f"   - Debes incluir barras de texto representativas utilizando caracteres tipo '████▒▒▒▒' de exactamente 8 caracteres totales.\n"
        f"4. Las justificaciones deben ser de exactamente 1 renglón.\n\n"
        f"Devuelve exactamente este formato premium:\n\n"
        f"🏟️ **INTELIGENCIA CONTEXTUAL Y SEDE:**\n"
        f"- Estadio: {estadio_real}\n"
        f"- Clima y Presión Atmosférica: [Detalle analítico]\n"
        f"- Índice de Fatiga por Viaje: [Cómputo analítico]\n"
        f"- Historial H2H Ponderado (Últimos 2 Años): [Tendencia de enfrentamientos]\n\n"
        f"📊 **DATOS AVANZADOS Y RENDIMIENTO COLECTIVO:**\n"
        f"- Goles Esperados (Proyección xG vs xGA):\n"
        f"  * {equipo_a}: [X.XX xG] | {equipo_b}: [X.XX xG]\n"
        f"- Auditoría de Bloque Táctico y Presión:\n"
        f"  * {equipo_a}: [Bloque Táctico] | {equipo_b}: [Bloque Táctico]\n"
        f"- Métricas de Posesión Efectiva (Último Tercio):\n"
        f"  * Dominio Territorial: [Barra de texto tipo ████▒▒▒▒] {equipo_a} XX% vs XX% {equipo_b}\n"
        f"- Mapeo de Transiciones Rápidas y Contraataques: [1 renglón táctico]\n\n"
        f"⏱️ **PRIMER TIEMPO (45 MINUTOS):**\n"
        f"- Goles (Over/Under 0.5):\n"
        f"  * Over: [Recuadro] [XX]% | Under: [Recuadro] [XX]%\n"
        f"  * Justificación: [1 renglón táctico]\n"
        f"- Córners (Over/Under 3.5):\n"
        f"  * Over: [Recuadro] [XX]% | Under: [Recuadro] [XX]%\n"
        f"  * Justificación: [1 renglón táctico]\n\n"
        f"⚽ **ANÁLISIS FINAL (90 MINUTOS):**\n"
        f"- Victoria Directa Favorito: [Nombre del Equipo] | [Recuadro] [XX]%\n"
        f"- Goles Globales (Over/Under 2.5):\n"
        f"  * Over: [Recuadro] [XX]% | Under: [Recuadro] [XX]%\n"
        f"  * Justificación: [1 renglón táctico]\n\n"
        f"📐 **CÓRNERS TOTALES EN EL PARTIDO:**\n"
        f"  * Over [8.5]: [Recuadro] [XX]% | Under [8.5]: [Recuadro] [XX]%\n"
        f"  * Desglose: {equipo_a}: X-Y corners / {equipo_b}: X-Y corners\n\n"
        f"🟨 **TARJETAS TOTALES Y ÁRBITRO:**\n"
        f"- Árbitro: {arbitro_real}\n"
        f"  * Over [3.5]: [Recuadro] [XX]% | Under [3.5]: [Recuadro] [XX]%\n"
        f"  * Justificación: [1 renglón táctico]\n\n"
        f"🎯 **EFECTIVIDAD EN MINUTOS CRÍTICOS:**\n"
        f"- Ventana Inicial (Minuto 1 al 15): [Tendencia]\n"
        f"- Ventana Final (Minuto 75 al 90): [Volumen]\n\n"
        f"🏹 **TIROS A PUERTA:**\n"
        f"  * Over [7.5]: [Recuadro] [XX]% | Under [7.5]: [Recuadro] [XX]%\n"
        f"  * Desglose: {equipo_a}: X-Y tiros directos | {equipo_b}: X-Y tiros directos"
    )
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_ia}],
        "temperature": 0.3,
        "max_tokens": 1500
    }
    
    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            bot.reply_to(message, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Inconveniente en el núcleo analítico estructural. {e}")

# =====================================================================
# 3. SECCIÓN: AUDITAR JUGADOR
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🏃‍♂️ Auditar Jugador")
def solicitar_jugador(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    USUARIOS_EN_ESPERA_JUGADOR[message.chat.id] = True
    bot.reply_to(
        message, 
        "📥 **MODO AUDITORÍA DE JUGADOR ACTIVO**\n"
        "Escribe directamente el nombre del jugador para mapear rendimiento en 2026.\n"
        "👉 *Ejemplo:* 'Santiago Giménez'"
    )

def procesar_auditoria_jugador_core(message):
    datos = message.text
    bot.reply_to(message, f"Auditando métricas de rendimiento real para: **{datos}**... ⚡")
    
    prompt_jugador = (
        f"Actúa como un algoritmo avanzado de Big Data y Scouting Internacional operando en el año 2026.\n"
        f"Evalúa el perfil, rol y estadísticas del jugador: {datos}.\n\n"
        f"🚨 FILTROS OBLIGATORIOS:\n"
        f"1. Analiza su situación actual y estadísticas reales de la temporada vigente.\n"
        f"2. CONTROL ESTRICTO DE POSICIÓN TÁCTICA REAL.\n\n"
        f"Devuelve exactamente este diseño limpio, sin notas extra:\n\n"
        f"🏃‍♂️ **AUDITORÍA DE JUGADOR: MOTOR DAMLEYT STRATEGY**\n"
        f"──────────────────────────────────────────────────\n"
        f"📋 **DATOS GENERALES:**\n"
        f"- Jugador: [Nombre completo]\n"
        f"- Estatus Actual: [Club y Selección 2026]\n"
        f"- Rol Proyectado: [Posición Real]\n\n"
        f"🎯 **MÉTRICAS DE TIRO A PUERTA:**\n"
        f"- ¿Logra al menos 1 tiro a pueta?: [🟩/🟨/🟥] [XX]%\n"
        f"- ¿Logra 2 o más tiros a puerta?: [🟩/🟨/🟥] [XX]%\n"
        f"- Tiros directos estimados: [Rango realista]\n"
        f"- Justificación de remate: [Explica la tendencia en 1 renglón]\n\n"
        f"⚽ **EFECTIVIDAD DE ANOTACIÓN:**\n"
        f"- Probabilidad de anotar en el partido: [🟩/🟨/🟥] [XX]%\n"
        f"- Estilo de Juego / Perfil Técnico: [Perfil preciso en 1 renglón]\n"
        f"──────────────────────────────────────────────────"
    )
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_jugador}],
        "temperature": 0.4,
        "max_tokens": 700
    }
    
    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            bot.reply_to(message, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al procesar métricas del jugador. {e}")

# =====================================================================
# 4. 🛡️ SECCIÓN CRÍTICA: COBERTURA EN VIVO (CERO TOLERANCIA A DATOS FALSOS)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🛡️ Cobertura en Vivo")
def solicitar_cobertura_partido(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    USUARIOS_EN_ESPERA_COBERTURA[message.chat.id] = True
    bot.reply_to(
        message, 
        "🛡️ **HEDGING TOOL: COBERTURA DE APUESTAS EN VIVO**\n"
        "Indique el partido activo para extraer su marcador e información real desde el servidor de datos.\n"
        "👉 *Ejemplo:* Costa de Marfil vs Alemania"
    )

def ejecutar_cobertura_live_core(message):
    partido_usuario = message.text.strip()
    bot.reply_to(message, f"Consultando estado en vivo en la API de Fútbol para: **{partido_usuario}**... ⚡")
    
    datos_api = obtener_datos_reales_partido(partido_usuario, es_live=True)
    
    # CONTROL INTERNO ABSOLUTO: Si no hay partido real en vivo detectado, se interrumpe la función de inmediato.
    if not datos_api or not datos_api.get("en_vivo"):
        bot.send_message(
            message.chat.id,
            f"❌ **MÓDULO LIVE: OPERACIÓN ABORTADA**\n"
            f"El servidor de la API de Fútbol no registra ningún partido activo en progreso para '{partido_usuario}' en este momento.\n\n"
            f"⚠️ *Nota de Seguridad:* El sistema de cobertura en vivo tiene prohibido generar proyecciones o estrategias basadas en simulaciones o datos fijos. Intente cuando el encuentro esté en juego."
        )
        return

    eq_a = datos_api["equipo_local"]
    eq_b = datos_api["equipo_visitante"]
    goles_a = datos_api["goles_local"]
    goles_b = datos_api["goles_visitante"]
    minuto_actual = datos_api["minuto"]
    estado_txt = datos_api["status_txt"]

    prompt_cobertura = (
        f"Actúa como un algoritmo matemático avanzado de arbitraje deportivo y hedging en tiempo real.\n"
        f"Genera una guía de cobertura analítica basada EXCLUSIVAMENTE en estos parámetros reales EXTRAÍDOS DE LA API DE FÚTBOL:\n"
        f"- Partido: {eq_a} vs {eq_b}\n"
        f"- Marcador Extraído en Vivo: {eq_a} {goles_a} - {goles_b} {eq_b}\n"
        f"- Minuto Extraído en Vivo: Minuto {minuto_actual} ({estado_txt})\n\n"
        f"🚨 REGLAS ESTRICTAS DE COBERTURA MATEMÁTICA:\n"
        f"1. Procesa únicamente la ventaja, desventaja o igualdad numérica real dictada por el marcador actual: {goles_a} a {goles_b}.\n"
        f"2. Queda ESTRICTAMENTE PROHIBIDO usar plantillas históricas, marcadores fijos (como 4-1) o minutos inventados.\n"
        f"3. Adapta las sugerencias operativas de contrapeso al minuto {minuto_actual}.\n\n"
        f"Genera exactamente esta respuesta estructurada:\n\n"
        f"🛡️ **Sugerencias de Cobertura (Hedging Tool) - Motor Damleyt Strategy**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ **Partido Monitoreado:** {eq_a} vs {eq_b}\n"
        f"⏱️ **Estado Real en Vivo:** Minuto {minuto_actual} | Marcador Actual: {goles_a} - {goles_b} ({estado_txt})\n\n"
        f"🎯 **ESTRATEGIA DE COBERTURA INMEDIATA:**\n"
        f"- Si tu línea inicial era favor de {eq_a}:\n"
        f"  * 🟢 Pick de Cobertura Live: [Línea técnica ajustada al marcador de {goles_a}-{goles_b} en el minuto {minuto_actual}]\n"
        f"  * 📊 Porcentaje de Capital a Reinvertir: [XX]% para resguardo de banca.\n\n"
        f"- Si tu línea inicial era favor de {eq_b} o mercados alternos:\n"
        f"  * 🔵 Pick de Cobertura Alterno: [Pick de contrapeso adaptado estrictamente al estado de juego]\n\n"
        f"💡 *Análisis Técnico:* [Análisis de 1 renglón enfocado en el desarrollo real de {goles_a} a {goles_b}].\n"
        f"──────────────────────────────────────────────────"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_cobertura}],
        "temperature": 0.0,  # Cero absoluto para eliminar cualquier tipo de alucinación del modelo
        "max_tokens": 700
    }

    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            bot.send_message(message.chat.id, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al calcular cobertura live. {e}")

# =====================================================================
# 5. SECCIÓN: PICKS PARA PARLEY
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🔥 Picks para Parley")
def menu_parley(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
        
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_bajo = types.KeyboardButton("🟩 Bajo Riesgo (3-8 Opciones)")
    btn_medio = types.KeyboardButton("🟨 Medio Riesgo (3-8 Opciones)")
    btn_alto = types.KeyboardButton("🟥 Alto Riesgo (3-8 Opciones)")
    markup.add(btn_bajo, btn_medio, btn_alto)
    bot.send_message(message.chat.id, "Seleccione el nivel de riesgo estratégico:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🟩 Bajo Riesgo (3-8 Opciones)", "🟨 Medio Riesgo (3-8 Opciones)", "🟥 Alto Riesgo (3-8 Opciones)"])
def procesar_parley(message):
    riesgo = "BAJO" if "Bajo" in message.text else "MEDIO" if "Medio" in message.text else "ALTO"
    msg_espera = bot.send_message(message.chat.id, f"⚡ Consultando matriz de datos para estructurar Parley de **{riesgo} RIESGO**...")

    prompt_parley = (
        f"Actúa como un auditor experto en apuestas deportivas operando en este año 2026.\n"
        f"Genera un Parley sugerido basado en partidos reales con perfil de riesgo {riesgo}.\n\n"
        f"Formateo de salida:\n\n"
        f"📊 **PARLEY SUGERIDO - RIESGO {riesgo}**\n"
        f"-----------------------------------------\n"
        f"1. [Partido Real] -> Selección: [Pick Variable] | Cuota Est.: [X.XX]\n"
        f"2. [Partido Real] -> Selección: [Pick Variable] | Cuota Est.: [X.XX]\n"
        f"3. [Partido Real] -> Selección: [Pick Variable] | Cuota Est.: [X.XX]\n"
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
        f"📈 **Momio Global Estimado:** [+XXX]\n"
        f"🎯 **Probabilidad de Acierto Numérica:** [XX]%"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_parley}],
        "temperature": 0.6
    }

    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            texto_parley = data['choices'][0]['message']['content']
            bot.delete_message(message.chat.id, msg_espera.message_id)
            bot.send_message(message.chat.id, texto_parley)
    except Exception as e:
        bot.send_message(message.chat.id, f"Aviso del sistema: Error al procesar matriz de parley. {e}")

# =====================================================================
# 6. GENERADOR AUTOMATIZADO DE TICKETS DE APUESTAS
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🎟️ Crear Ticket")
def simular_ticket_apuesta(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    
    bot.reply_to(message, "🎟️ Compilando selecciones de alto valor basadas en partidos programados... ⚡")

    prompt_ticket = (
        f"Actúa como un algoritmo experto de la suite Damleyt Data Analytics operando en este año 2026.\n"
        f"Genera un ticket de inversión simulado combinando 3 selecciones de alto valor basadas en partidos reales de fútbol.\n\n"
        f"Usa exactamente este formato de salida limpio:\n\n"
        f"🎟️ **TICKET DE INVERSIÓN: DAMLEYT STRATEGY**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ [Partido Real 1]\n"
        f"🔹 Selección: [Pick] | Cuota: [X.XX]\n\n"
        f"🏟️ [Partido Real 2]\n"
        f"🔹 Selección: [Pick] | Cuota: [X.XX]\n\n"
        f"🏟️ [Partido Real 3]\n"
        f"🔹 Selección: [Pick] | Cuota: [X.XX]\n"
        f"──────────────────────────────────────────────────\n"
        f"🛡️ **SUGERENCIA DE COBERTURA GENERAL:**\n"
        f"- [Instrucción técnica operativa en 1 renglón]\n\n"
        f"📊 **MÉTRICAS DEL TICKET:**\n"
        f"- Momio Total Proyectado: [+XXX / X.XX]\n"
        f"- Nivel de Confianza: [🟩/🟨] [XX]%\n"
        f"- Recommendation Stake: Stk [X/10]\n"
        f"──────────────────────────────────────────────────"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_ticket}],
        "temperature": 0.6,
        "max_tokens": 800
    }

    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            bot.send_message(message.chat.id, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al actuar ticket digital. {e}")

# =====================================================================
# 7. MÓDULO EXCLUSIVO: ESCENARIOS LIVE & VALUE-BET CALCULATOR
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "📉 Escenarios Live & Value")
def simular_escenarios_live(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    
    bot.reply_to(message, "📊 Calculando desviaciones de cuotas de mercado (Value-Bets) y Simulación Live... ⚡")

    prompt_live = (
        f"Actúa como una calculadora de apuestas de valor operando en este año 2026.\n"
        f"Simula un escenario de partido dinámico ante variaciones en vivo con cuadre perfecto del 100%.\n\n"
        f"Devuelve exactamente esta estructura:\n\n"
        f"📉 **SIMULACIÓN DE ESCENARIOS LIVE (MINUTO 15)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ Partido Proyectado: [Partido Real]\n"
        f"🚨 Escenario Dinámico: Ajuste de líneas por desarrollo inicial.\n"
        f"- Cambio de Mercado en Vivo:\n"
        f"  * Línea de Córners: Proyección Over [X.X] (Probabilidad: 🟩 [XX]% | Under: 🟥 [XX]%)\n"
        f"  * Ajuste de Hándicap Asiático Óptimo: [Línea sugerida]\n\n"
        f"🎯 **CALCULADORA DE VALOR (VALUE-BET DETECTOR)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🔹 Mercado Detectado: [Mercado Específico]\n"
        f"- Probabilidad del Motor IA: 🟩 [XX]%\n"
        f"- Cuota Justa (Matemática): [X.XX]\n"
        f"- Cuota Promedio en Bookies: [X.XX]\n"
        f"- Margen de Ventaja Real: [+XX.X%]"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_live}],
        "temperature": 0.5,
        "max_tokens": 800
    }

    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            bot.send_message(message.chat.id, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al calcular matrices de valor live. {e}")

# =====================================================================
# 8. MÓDULO EXCLUSIVO: ALERTAS PRE-MATCH
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "📢 Alertas Pre-Match")
def enviar_alertas_prematch(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    
    bot.reply_to(message, "📢 Extrayendo alertas críticas de última hora (Lesiones, Cuotas y Clima)... ⚡")

    prompt_alertas = (
        f"Actúa como un analista de riesgos deportivos operando en este año 2026.\n"
        f"Genera un reporte de alertas Pre-Match basado en partidos reales de fútbol de la temporada actual.\n\n"
        f"Devuelve exactamente esta estructura limpia:\n\n"
        f"📢 **ALERTAS PRE-MATCH Y RIESGO DE INVERSIÓN**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ Partido Bajo Alerta: [Partido Real]\n"
        f"🚨 Reporte de Última Hora: [Detalle de baja o clima en 1 renglón]\n"
        f"- Impacto en el Mercado:\n"
        f"  * Línea de Dinero: [Variación estimada del momio]\n"
        f"  * Ajuste de Goles Proyectados: [Tendencia Over/Under]\n\n"
        f"📉 **ALERTAS ADICIONALES (VOLUMEN EN CASAS DE APUESTAS)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🔹 Movimiento Anómalo: [Mercado inflado en 1 renglón]\n"
        f"- Recommendation Operativa: [Consejo de control de stake en 1 renglón]"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_alertas}],
        "temperature": 0.5,
        "max_tokens": 700
    }

    try:
        requests_response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = requests_response.json()
        if 'choices' in data:
            bot.send_message(message.chat.id, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al calcular alertas pre-match. {e}")

# =====================================================================
# 🔄 RECEPTOR GENERAL DE TEXTO (GESTIÓN DE ESTADOS DE ENTRADA)
# =====================================================================
@bot.message_handler(func=lambda message: True)
def manejar_entradas_texto(message):
    chat_id = message.chat.id
    
    if chat_id in USUARIOS_EN_ESPERA_PARTIDO:
        del USUARIOS_EN_ESPERA_PARTIDO[chat_id]
        ejecutar_auditoria_core(message, message.text)
        
    elif chat_id in USUARIOS_EN_ESPERA_JUGADOR:
        del USUARIOS_EN_ESPERA_JUGADOR[chat_id]
        procesar_auditoria_jugador_core(message)
        
    elif chat_id in USUARIOS_EN_ESPERA_COBERTURA:
        del USUARIOS_EN_ESPERA_COBERTURA[chat_id]
        ejecutar_cobertura_live_core(message)
        
    else:
        bot.reply_to(message, "⚠️ Opción no reconocida. Por favor, utiliza los botones del menú inferior o escribe /start para reiniciar la interfaz.")

# =====================================================================
# 🚀 EJECUCIÓN INICIAL Y CONTROL DE HILOS
# =====================================================================
if __name__ == "__main__":
    hilo_servidor = threading.Thread(target=iniciar_servidor_render)
    hilo_servidor.daemon = True
    hilo_servidor.start()
    
    print("🤖 DAMLEYT CORE: Bot iniciado correctamente y listo para operar.")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Caída detectada en polling: {e}. Reiniciando bucle en 5 segundos...")
            time.sleep(5)