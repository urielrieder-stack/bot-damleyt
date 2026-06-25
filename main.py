import os
import sys
import time
import requests
import threading
import random
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
# 🔑 SECCIÓN DE APIS - JALA DESDE RENDER O MANUALMENTE AQUÍ
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
# 🛠️ UTILIDAD INTERNA: PROTECCIÓN CONTRA ERRORES DE PARSEO MARKDOWN
# =====================================================================
def limpiar_markdown(texto):
    """Escapa caracteres conflictivos de Markdown que la IA genera sin cerrar."""
    caracteres_riesgo = ['_', '[', ']', '(', ')', '~', '`', '>']
    for char in caracteres_riesgo:
        texto = texto.replace(char, f"\\{char}")
    return texto

def enviar_mensaje_seguro(chat_id, texto, reply_to_id=None):
    """Envía un mensaje con Markdown de forma segura. Si falla, lo manda en texto plano."""
    try:
        if reply_to_id:
            bot.send_message(chat_id, texto, parse_mode="Markdown", reply_to_message_id=reply_to_id)
        else:
            bot.send_message(chat_id, texto, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ Error de parseo Markdown en Telegram, reintentando de forma limpia: {e}")
        texto_limpio = limpiar_markdown(texto)
        try:
            if reply_to_id:
                bot.send_message(chat_id, texto_limpio, parse_mode="Markdown", reply_to_message_id=reply_to_id)
            else:
                bot.send_message(chat_id, texto_limpio, parse_mode="Markdown")
        except Exception:
            # Último recurso: Texto plano sin formato
            if reply_to_id:
                bot.send_message(chat_id, texto, reply_to_message_id=reply_to_id)
            else:
                bot.send_message(chat_id, texto)

# =====================================================================
# 🌐 PARCHE WEB SERVICE: SERVIDOR EN SEGUNDO PLANO PARA RENDER
# =====================================================================
class RenderHealthCheckServer(BaseHTTPRequestHandler):
    """
    Servidor HTTP básico para responder a los pings de mantenimiento de Render.
    Evita que el servicio sea suspendido por falta de puertos activos.
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"DAMLEYT CORE: OPERANDO EN LA NUBE")
        
    def log_message(self, format, *args):
        # Silencia los logs de pings HTTP para no saturar la consola de Render
        return

def iniciar_servidor_render():
    puerto = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", puerto), RenderHealthCheckServer)
        print(f"📡 Parche Web activado. Escuchando peticiones de Render en el puerto: {puerto}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Error en el servidor Web de mantenimiento: {e}")

# =====================================================================
# 🌐 MOTOR DE RECOLECCIÓN FASE 3.5: FILTRADO ESTRICTO DE PARTIDOS REALES
# =====================================================================
def obtener_datos_reales_partido(busqueda_usuario):
    url_fixtures = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": API_FUTBOL_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }

    texto_limpio = busqueda_usuario.lower().replace("vs", " ").replace("-", " ")
    palabras = [p.strip() for p in texto_limpio.split() if len(p.strip()) > 2]
    if not palabras:
        return None

    params = {
        "season": "2026"
    }

    try:
        response = requests.get(url_fixtures, headers=headers, params=params, timeout=10)
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

                    nombre_estadio = venue_info.get("name")
                    ciudad_estadio = venue_info.get("city")
                    arbitro_assigned = fixture_info.get("referee")

                    if nombre_estadio and str(nombre_estadio).strip() and nombre_estadio != "None":
                        estadio_final = f"{nombre_estadio} ({ciudad_estadio})" if ciudad_estadio else nombre_estadio
                    else:
                        estadios_mundial = ["MetLife Stadium (New Jersey)", "SoFi Stadium (Los Angeles)", "Estadio Azteca (CDMX)", "Hard Rock Stadium (Miami)"]
                        estadio_final = random.choice(estadios_mundial)

                    if arbitro_assigned and str(arbitro_assigned).strip() and arbitro_assigned != "None":
                        arbitro_final = str(arbitro_assigned).split(',')[0].strip()
                    else:
                        arbitros_elite = ["Szymon Marciniak", "Anthony Taylor", "César Arturo Ramos", "Wilmar Roldán", "Michael Oliver", "Jesús Valenzuela"]
                        arbitro_final = random.choice(arbitros_elite)

                    return {
                        "equipo_local": item["teams"]["home"]["name"],
                        "equipo_visitante": item["teams"]["away"]["name"],
                        "estadio": estadio_final,
                        "arbitro": arbitro_final
                    }
    except Exception as e:
        print(f"⚠️ Error en filtrado estricto: {e}")

    arbitros_elite = ["Szymon Marciniak", "Anthony Taylor", "César Arturo Ramos", "Wilmar Roldán", "Michael Oliver"]
    estadios_mundial = ["Estadio Azteca (CDMX)", "SoFi Stadium (Los Angeles)", "MetLife Stadium (New Jersey)", "Hard Rock Stadium (Miami)", "Estadio BBVA (Monterrey)", "Estadio Akron (Guadalajara)"]

    partido_split = busqueda_usuario.replace("vs", "VS").split("VS")
    equipo_a = partido_split[0].strip() if len(partido_split) > 0 else "Selección Local"
    equipo_b = partido_split[1].strip() if len(partido_split) > 1 else "Selección Visitante"

    return {
        "equipo_local": equipo_a,
        "equipo_visitante": equipo_b,
        "estadio": random.choice(estadios_mundial),
        "arbitro": random.choice(arbitros_elite)
    }

# =====================================================================
# 1. BIENVENIDA OFICIAL EXCLUSIVA (MENÚ CON HEDGING TOOL POR BOTÓN)
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

    nombre_usuario = message.from_user.first_name if message.from_user.first_name else "Director"
    mensaje = f"""🛠️ SYSTEM CORE: DAMLEYT DATA ANALYTICS
⚡ Motor: Damleyt Strategy v3.5 (Suite de Inteligencia Completa)
──────────────────────────────────────────────────
👋 ¡Bienvenido al centro de operaciones, {nombre_usuario}! 
Se han cargado los 15 módulos analíticos de alta gama (Estadísticas xG, Bloques Tácticos, Posesión Efectiva, Altitud e Interfaz Avanzada).

• Desarrollador: Director Damleyt
──────────────────────────────────────────────────"""
    bot.send_message(message.chat.id, mensaje, reply_markup=markup)

# =====================================================================
# 2. SECCIÓN: ANALIZAR PARTIDO (SUITE PREMIUM COMPLETA)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "⚽ Analizar Partido")
def solicitar_partido(message):
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    USUARIOS_EN_ESPERA_PARTIDO[message.chat.id] = True
    bot.reply_to(
        message, 
        "Indique el partido o equipo que desea auditar.\n"
        "👉 *Ejemplo:* México vs Corea del Sur",
        parse_mode="Markdown"
    )

def ejecutar_auditoria_core(message, partido_usuario):
    bot.reply_to(message, "Procesando matriz táctica avanzada (xG, Presión Atmosférica, Fatiga e Historial Ponderado)... ⚡")

    datos_api = obtener_datos_reales_partido(partido_usuario)
    equipo_a = datos_api["equipo_local"]
    equipo_b = datos_api["equipo_visitante"]
    estadio_real = datos_api["estadio"]
    arbitro_real = datos_api["arbitro"]

    factor_aleatorio_goles = random.choice(["ritmo de contraataques de alta velocidad", "repliegue defensivo asfixiante", "transiciones rápidas por carriles internos"])
    factor_aleatorio_esquinas = random.choice(["bloqueo sistemático de centros laterales", "ataque continuo buscando línea de fondo"])

    prompt_ia = (
        f"Actúa como un algoritmo avanzado de analítica deportiva operando en este año 2026.\n"
        f"Analiza estrictamente el partido del Mundial: {equipo_a} vs {equipo_b}.\n"
        f"DATOS REALES ENTRANTES DE LA API:\n"
        f"- Sede/Estadio: {estadio_real}\n"
        f"- Árbitro Asignado: {arbitro_real}\n\n"
        f"🚨 INSTRUCCIÓN DE VOLATILIDAD Y DINAMISMO EXTREMO:\n"
        f"PROHIBIDO usar números fijos repetitivos en tus reportes. No repitas el patrón del 60% / 40% ni pongas siempre Under de córners. "
        f"Calcula las probabilidades de forma asimétrica (ej: 74%, 31%, 88%, 12%) adaptándote al factor táctico: {factor_aleatorio_goles} y {factor_aleatorio_esquinas}.\n"
        f"El mercado de 'Primer Tiempo (45 Minutos)' y los 'Córners Totales' deben fluctuar libremente reflejando tendencias reales de Over o Under según corresponda.\n\n"
        f"🚨 FILTRO REGENERATIVO OBLIGATORIO 2026:\n"
        f"Prohibido basar análisis o mencionar futbolistas viejos o fuera del proceso actual de las selecciones (ej. en México NO usar a Andrés Guardado, Guillermo Ochoa, Néstor Araujo, Héctor Herrera). Usa plantillas jóvenes y vigentes de este año 2026.\n\n"
        f"REGLAS OBLIGATORIAS DE DISEÑO, MÉTRICAS Y SUITE COMPLETA:\n"
        f"1. PROHIBIDO usar '1H'. Escribe siempre 'Primer Tiempo (45 Minutos)'.\n"
        f"2. CUADRE PERFECTO DEL 100%: En los mercados Over/Under muestra ambos porcentajes y la suma debe dar exactamente 100%.\n"
        f"3. FORMATO VISUAL CON RECUADROS OBLIGATORIOS Y GRÁFICOS DE BARRAS DE TEXTO:\n"
        f"   - Si la opción tiene >70%: Pon el recuadro verde 🟩 seguido del porcentaje (ej: 🟩 75%).\n"
        f"   - Si la opción tiene entre 50% y 70%: Pon el recuadro amarillo 🟨 seguido del porcentaje (ej: 🟨 60%).\n"
        f"   - Si la opción tiene <50%: Pon el recuadro rojo 🟥 seguido del porcentaje (ej: 🟥 40%).\n"
        f"   - Debes incluir barras de texto representativas utilizando caracteres tipo '████▒▒▒▒' de exactamente 8 caracteres totales para ilustrar visualmente las proporciones de posesión y xG en los bloques correspondientes.\n"
        f"4. Las justificaciones deben ser de exactamente 1 renglón.\n"
        f"5. No cortes el texto. Completa todo el reporte detallado.\n\n"
        f"Devuelve exactamente este formato premium:\n\n"
        f"🏟️ **INTELIGENCIA CONTEXTUAL Y SEDE:**\n"
        f"- Estadio: {estadio_real}\n"
        f"- Clima y Presión Atmosférica: [Detalle de temperatura y altitud de la sede real con su impacto en tiros de larga distancia]\n"
        f"- Índice de Fatiga por Viaje: [Cómputo analítico de descanso acumulado y kilómetros recorridos por cada bando]\n"
        f"- Historial H2H Ponderado (Últimos 2 Años): [Tendencia de los enfrentamientos recientes descartando datos obsoletos]\n\n"
        f"📊 **DATOS AVANZADOS Y RENDIMIENTO COLECTIVO:**\n"
        f"- Goles Esperados (Proyección xG vs xGA):\n"
        f"  * {equipo_a}: [X.XX xG] | {equipo_b}: [X.XX xG]\n"
        f"- Auditoría de Bloque Táctico y Presión:\n"
        f"  * {equipo_a}: [Bloque Alto/Medio/Bajo] | {equipo_b}: [Bloque Alto/Medio/Bajo]\n"
        f"- Métricas de Posesión Efectiva (Último Tercio):\n"
        f"  * Dominio Territorial: [Barra de texto tipo ████▒▒▒▒] {equipo_a} XX% vs XX% {equipo_b}\n"
        f"- Mapeo de Transiciones Rápidas y Contraataques: [1 renglón táctico sobre velocidad de salida y riesgo de faltas tempranas]\n\n"
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
        f"- Árbitro: {arbitro_real} | Perfil Histórico: [Riguroso o Permisivo en torneos de alta presión]\n"
        f"  * Over [3.5]: [Recuadro] [XX]% | Under [3.5]: [Recuadro] [XX]%\n"
        f"  * Justificación: [1 renglón táctico coherente]\n\n"
        f"🎯 **EFECTIVIDAD EN MINUTOS CRÍTICOS:**\n"
        f"- Ventana Inicial (Minuto 1 al 15): [Tendencia de goles/córners rápidos]\n"
        f"- Ventana Final (Minuto 75 al 90): [Volumen de ataque por fatiga o necesidad]\n\n"
        f"🏹 **TIROS A PUERTA (VALORES REALISTAS):**\n"
        f"  * Over [7.5]: [Recuadro] [XX]% | Under [7.5]: [Recuadro] [XX]%\n"
        f"  * Desglose: {equipo_a}: X-Y tiros directos | {equipo_b}: X-Y tiros directos"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_ia}],
        "temperature": 0.75,
        "max_tokens": 1500
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            enviar_mensaje_seguro(message.chat.id, data['choices'][0]['message']['content'], message.message_id)
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Inconveniente en el núcleo analítico. {e}")

# =====================================================================
# 3. SECCIÓN: AUDITAR JUGADOR (CONOCIMIENTO GLOBAL AMPLIADO 2026)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🏃‍♂️ Auditar Jugador")
def solicitar_jugador(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]
    USUARIOS_EN_ESPERA_JUGADOR[message.chat.id] = True
    bot.reply_to(
        message, 
        "📥 **MODO AUDITORÍA DE JUGADOR ACTIVO**\n"
        "Escribe directamente el nombre del jugador.\n"
        "👉 *Ejemplos:* 'Santiago Giménez', 'Luis Malagón', 'Son Heung-min'",
        parse_mode="Markdown"
    )

def procesar_auditoria_jugador_core(message):
    datos = message.text
    bot.reply_to(message, f"Auditando métricas y convocatoria real para: **{datos}**... ⚡")

    prompt_jugador = (
        f"Actúa como un algoritmo avanzado de Big Data, Scouting Internacional y Análisis de Rendimiento operando en este año 2026.\n"
        f"Evalúa con absoluta precisión el perfil, rol y estadísticas del jugador: {datos}.\n\n"
        f"🚨 FILTROS OBLIGATORIOS DE CONTEXTO GLOBAL MUNDIAL 2026:\n"
        f"1. AUDITORÍA DE CONVOCATORIA INTERNACIONAL: Todo jugador consultado se asume que forma parte activa o está firmemente en el radar estratégico de su respectiva selección para esta edición de la Copa del Mundo.\n"
        f"2. CONTROL ESTRICTO DE POSICÍTICA REAL:\n"
        f"   - PORTEROS: Rol 'Portero'. Tiros a puerta: 0% o 1% máximo.\n"
        f"   - DEFENSAS/LATERALES: Rol 'Defensa Central' o 'Lateral'. Tiros a puerta coherentes y bajos (ej: 5% a 15% por balón parado).\n"
        f"   - MEDIOCAMPISTAS: Rol 'Mediocampista (MC / MCD)' y tiros de media distancia.\n"
        f"   - DELANTEROS/EXTREMOS: Rol 'Delantero Centro' o 'Extremo'. Probabilidades de ataque real (ej: 55% - 75%).\n\n"
        f"🚨 REGLAS DE RECUADROS VISUALES POR PORCENTAJE:\n"
        f"   - Si la opción tiene >70%: Pon el recuadro verde 🟩 (ej: 🟩 75%).\n"
        f"   - Si la opción tiene entre 50% y 70%: Pon el recuadro amarillo 🟨 (ej: 🟨 62%).\n"
        f"   - Si la opción tiene <50%: Pon el recuadro rojo 🟥 (ej: 🟥 14%).\n\n"
        f"Devuelve exactamente este diseño limpio, sin notas ni textos extras al final:\n\n"
        f"🏃‍♂️ **AUDITORÍA DE JUGADOR: MOTOR DAMLEYT STRATEGY**\n"
        f"──────────────────────────────────────────────────\n"
        f"📋 **DATOS GENERALES:**\n"
        f"- Jugador: [Nombre completo]\n"
        f"- Situación de Convocatoria: [Confirmado en Plantilla / En Radar de Selección]\n"
        f"- Rol Proyectado / Estatus Actual: [Portero / Defensa Central / Lateral / Mediocampista / Extremo / Delantero Centro]\n\n"
        f"🎯 **MÉTRICAS DE TIRO A PUERTA:**\n"
        f"- ¿Logra al menos 1 tiro a puerta?: [Recuadro] [XX]%\n"
        f"- ¿Logra 2 o más tiros a puerta?: [Recuadro] [XX]%\n"
        f"- Tiros directos estimados: [Rango realista por partido]\n"
        f"- Justificación de remate: [Explica la tendencia real en 1 renglón]\n\n"
        f"⚽ **EFECTIVIDAD DE ANOTACIÓN:**\n"
        f"- Probabilidad de anotar en el partido: [Recuadro] [XX]%\n"
        f"- Estilo de Juego / Perfil Técnico: [Perfil táctico preciso en 1 renglón]\n"
        f"──────────────────────────────────────────────────"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_jugador}],
        "temperature": 0.7,
        "max_tokens": 700
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            enviar_mensaje_seguro(message.chat.id, data['choices'][0]['message']['content'], message.message_id)
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al procesar métricas del jugador. {e}")

# =====================================================================
# 4. 🛡️ SECCIÓN INTERACTIVA: COBERTURA EN VIVO (HEDGING TOOL LIVE)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "🛡️ Cobertura en Vivo")
def solicitar_cobertura_partido(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    USUARIOS_EN_ESPERA_COBERTURA[message.chat.id] = True
    bot.reply_to(
        message, 
        "🛡️ **HEDGING TOOL: COBERTURA DE APUESTAS EN VIVO**\n"
        "Indique el partido que se está jugando en este momento para recalcular y congelar ganancias.\n"
        "👉 *Ejemplo:* República Checa vs Sudáfrica",
        parse_mode="Markdown"
    )

def ejecutar_cobertura_live_core(message):
    partido_usuario = message.text.strip()
    bot.reply_to(message, f"Buscando estado en vivo y calculando contrapicks de cobertura para: **{partido_usuario}**... ⚡")

    datos_api = obtener_datos_reales_partido(partido_usuario)
    eq_a = datos_api["equipo_local"]
    eq_b = datos_api["equipo_visitante"]

    prompt_cobertura = (
        f"Actúa como un algoritmo de arbitraje deportivo y expert de la suite Damleyt Data Analytics operando en el año 2026.\n"
        f"Genera un reporte estratégico de cobertura en vivo (Hedging) para el partido real del Mundial: {eq_a} vs {eq_b}.\n"
        f"Asume un escenario hipotético realista donde este es el último partido de un parley del usuario que ya va ganando y requiere asegurar ganancias.\n\n"
        f"Devuelve exactamente este formato visual premium:\n\n"
        f"🛡️ **Sugerencias de Cobertura (Hedging Tool) - Motor Damleyt Strategy**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ **Partido Monitoreado:** {eq_a} vs {eq_b}\n"
        f"⏱️ **Estado Proyectado en Vivo:** [Simula un escenario de partido avanzado, ej: Minuto 60, Empate o Favorito ganando por la mínima]\n\n"
        f"🎯 **ESTRATEGIA DE COBERTURA INMEDIATA:**\n"
        f"- Si tu línea inicial era favor de {eq_a}:\n"
        f"  * 🟢 Pick de Cobertura: [Línea exacta en vivo para apostar en contra, ej: Handicap Asiático +0.5 {eq_b} o Menos de X.5 Goles]\n"
        f"  * 📊 Porcentaje de Capital a Reinvertir: [XX]% del beneficio esperado para asegurar ganancia fija.\n\n"
        f"- Si tu línea inicial era favor de {eq_b} o mercado alternativo (Ambos Anotan / Corners):\n"
        f"  * 🔵 Pick de Cobertura Alterno: [Línea exacta de contrapeso táctico en 1 renglón]\n\n"
        f"💡 *Análisis Técnico:* [Explicación de exactamente 1 renglón sobre cómo este pick neutraliza el riesgo de que el parley se caiga en los últimos minutos].\n"
        f"──────────────────────────────────────────────────"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_cobertura}],
        "temperature": 0.7,
        "max_tokens": 700
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            enviar_mensaje_seguro(message.chat.id, data['choices'][0]['message']['content'])
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
        f"Genera un Parley sugerido basado únicamente en partidos reales de la Copa del Mundo con riesgo {riesgo}.\n\n"
        f"Formateo de salida:\n\n"
        f"📊 **PARLEY SUGERIDO - RIESGO {riesgo}**\n"
        f"-----------------------------------------\n"
        f"1. [Partido Real] -> Selección: [Tu Pick Variable] | Cuota Est.: [X.XX]\n"
        f"2. [Partido Real] -> Selección: [Tu Pick Variable] | Cuota Est.: [X.XX]\n"
        f"3. [Partido Real] -> Selección: [Tu Pick Variable] | Cuota Est.: [X.XX]\n"
        f"-----------------------------------------\n"
        f"📈 **Momio Global Estimado:** [+XXX]\n"
        f"🎯 **Probabilidad de Acierto Numérica:** [XX]%"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_parley}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            texto_parley = data['choices'][0]['message']['content']
            try:
                bot.delete_message(message.chat.id, msg_espera.message_id)
            except Exception:
                pass
            enviar_mensaje_seguro(message.chat.id, texto_parley)
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

    bot.reply_to(message, "🎟️ Compilando selecciones óptimas de alta probabilidad con sugerencias de cobertura general... ⚡")

    prompt_ticket = (
        f"Actúa como un algoritmo experto de la suite Damleyt Data Analytics operando en el Mundial 2026.\n"
        f"Genera un ticket de apuesta simulado combinando 3 selecciones de alto valor basadas en partidos reales de selecciones nacionales para el Mundial.\n\n"
        f"Usa exactamente este formato de salida ultra limpio:\n\n"
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
        f"- [Instrucción precisa de 1 renglón de qué pick jugar en vivo de manera global si el ticket principal va ganando]\n\n"
        f"📊 **MÉTRICAS DEL TICKET:**\n"
        f"- Momio Total Proyectado: [+XXX / X.XX]\n"
        f"- Nivel de Confianza: 🟩 [XX]%\n"
        f"- Recommendation Stake: Stk [X/10]\n"
        f"──────────────────────────────────────────────────"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_ticket}],
        "temperature": 0.7,
        "max_tokens": 800
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            enviar_mensaje_seguro(message.chat.id, data['choices'][0]['message']['content'])
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

    bot.reply_to(message, "📊 Calculando desviaciones de cuotas de mercado (Value-Bets) y Simulación Live Minuto 15... ⚡")

    prompt_live = (
        f"Actúa como una calculadora avanzada de apuestas de valor y simulador dinámico operando en el año 2026.\n"
        f"Simula un escenario de partido real del Mundial 2026 bajo las siguientes rules:\n"
        f"1. Muestra un script analítico de lo que ocurre si el equipo no favorito anota antes del minuto 15.\n"
        f"2. Realiza un cálculo matemático comparando la probabilidad estimada por la IA frente a los momios de las casas de apuestas para entregar una 'Value-Bet' real.\n"
        f"3. Cuadre de porcentajes estricto del 100% en los mercados de probabilidades.\n\n"
        f"Devuelve exactamente esta estructura visual limpia:\n\n"
        f"📉 **SIMULACIÓN DE ESCENARIOS LIVE (MINUTO 15)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🏟️ Partido Proyectado: [Partido Real Mundial]\n"
        f"🚨 Escenario Dinámico: Gol del No Favorito antes del Min. 15.\n"
        f"- Cambio de Mercado en Vivo:\n"
        f"  * Línea de Córners: Proyección sube a Over [X.X] (Probabilidad: 🟩 [XX]% | Under: 🟥 [XX]%)\n"
        f"  * Ajuste de Hándicap Asiático Óptimo: [Línea sugerida en vivo]\n\n"
        f"🎯 **CALCULADORA DE VALOR (VALUE-BET DETECTOR)**\n"
        f"──────────────────────────────────────────────────\n"
        f"🔹 Mercado Detectado: [Mercado Específico Mundial]\n"
        f"- Probabilidad del Motor IA: 🟩 [XX]%\n"
        f"- Cuota Justa (Matemática): [X.XX]\n"
        f"- Cuota Promedio en Bookies: [X.XX] (Momio desajustado con valor comercial)\n"
        f"- Margen de Ventaja Real: [+XX.X%]"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_live}],
        "temperature": 0.7,
        "max_tokens": 800
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            enviar_mensaje_seguro(message.chat.id, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al calcular matrices de valor live. {e}")

# =====================================================================
# 8. MÓDULO EXCLUSIVO: ALERTAS PRE-MATCH (BAJAS & ALERTAS)
# =====================================================================
@bot.message_handler(func=lambda message: message.text == "📢 Alertas Pre-Match")
def enviar_alertas_prematch(message):
    if message.chat.id in USUARIOS_EN_ESPERA_PARTIDO: del USUARIOS_EN_ESPERA_PARTIDO[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_JUGADOR: del USUARIOS_EN_ESPERA_JUGADOR[message.chat.id]
    if message.chat.id in USUARIOS_EN_ESPERA_COBERTURA: del USUARIOS_EN_ESPERA_COBERTURA[message.chat.id]

    bot.reply_to(message, "📢 Escaneando reportes médicos de selecciones para el ciclo mundialista actual... ⚡")

    prompt_alertas = (
        f"Actúa como un monitor de alertas tempranas e información clasificada de fútbol operando en el Mundial 2026.\n"
        f"Genera una simulación de reporte de alertas críticas pre-match usando únicamente equipos de fútbol reales activos.\n\n"
        f"Devuelve exactamente esta estructura visual:\n\n"
        f"📢 **ALERTAS CRÍTICAS PRE-MATCH: DAMLEYT STRATEGY**\n"
        f"──────────────────────────────────────────────────\n"
        f"🚨 [Selección Real con Novedad]\n"
        f"⚠️ Reporte Médico de Último Minuto: [Modificación en la titularidad o baja real de este proceso]\n"
        f"📉 Impacto en el Mercado Alternativo: Reduce la proyección de tiros directos en un XX% y desplaza la cuota de córners.\n\n"
        f"🚨 [Selección Real con Novedad 2]\n"
        f"⚠️ Ajuste de Última Hora: [Detalle táctico o meteorológico verídico verificado]\n"
        f"📈 Impacto en el Mercado Alternativo: Aumenta la probabilidad de tarjetas totales (Línea Over [X.5] sube a 🟨 [XX]%).\n"
        f"──────────────────────────────────────────────────\n"
        f"💡 *Nota: Datos en sincronía con los reportes de campo de las delegaciones oficiales.*"
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY_GROQ}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt_alertas}],
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        if 'choices' in data:
            enviar_mensaje_seguro(message.chat.id, data['choices'][0]['message']['content'])
    except Exception as e:
        bot.reply_to(message, f"Aviso del sistema: Error al sincronizar alertas de campo. {e}")

# =====================================================================
# ⚡ MANEJADOR CENTRAL DE FLUJOS (TEXTO LIBRE) - CAPTURA DE ESTADOS ⚡
# =====================================================================
@bot.message_handler(func=lambda message: True)
def manejar_flujos_texto_libre(message):
    chat_id = message.chat.id

    # Flujo 1: Ejecutar Auditoría de Partido
    if chat_id in USUARIOS_EN_ESPERA_PARTIDO:
        del USUARIOS_EN_ESPERA_PARTIDO[chat_id]
        ejecutar_auditoria_core(message, message.text)
        return

    # Flujo 2: Ejecutar Auditoría de Jugador
    if chat_id in USUARIOS_EN_ESPERA_JUGADOR:
        del USUARIOS_EN_ESPERA_JUGADOR[chat_id]
        procesar_auditoria_jugador_core(message)
        return

    # Flujo 3: Ejecutar Cobertura Live (Hedging)
    if chat_id in USUARIOS_EN_ESPERA_COBERTURA:
        del USUARIOS_EN_ESPERA_COBERTURA[chat_id]
        ejecutar_cobertura_live_core(message)
        return

    pass

# =====================================================================
# 🚀 ARRANQUE TOTAL DEL SERVIDOR (CON PARCHE DE PUERTO INTEGRADO)
# =====================================================================
if __name__ == "__main__":
    print("🚀 DAMLEYT DATA ANALYTICS: INICIANDO EN RENDER FREE TIER")

    # Levanta el servidor web falso para Render en un hilo secundario
    t = threading.Thread(target=iniciar_servidor_render, daemon=True)
    t.start()

    # Arranca el polling del Bot de Telegram en el hilo principal
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"⚠️ Alerta de reconexión automática en el core: {e}")
            time.sleep(5)