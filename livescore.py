import os
import requests
from datetime import datetime, timedelta
import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext

# --- CONFIGURAZIONE ---
# Inserisci qui i tuoi token
TELEGRAM_TOKEN = ' 8448591154:AAEJorp4NLnox6coY3zaB9iRu5p0h2jTLss'
FOOTBALL_DATA_TOKEN = '437bdfc679224878ad25e2d8cff723a0'

# ID della Serie A su football-data.org
SERIE_A_ID = 2019

# URL base dell'API e header per l'autenticazione
BASE_API_URL = 'http://api.football-data.org/v4/'
HEADERS = {'X-Auth-Token': FOOTBALL_DATA_TOKEN}

# --- FUNZIONI PER INTERAGIRE CON L'API ---

def fetch_data(endpoint):
    """Funzione generica per recuperare dati dall'API."""
    try:
        response = requests.get(BASE_API_URL + endpoint, headers=HEADERS)
        response.raise_for_status()  # Solleva un'eccezione per errori HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore API: {e}")
        return None

# --- COMANDI DEL BOT ---

def start(update: telegram.Update, context: CallbackContext):
    """Messaggio di benvenuto e lista comandi."""
    user = update.effective_user
    welcome_message = (
        f"Ciao {user.first_name}!\n\n"
        "Sono il tuo bot per la Serie A. Ecco cosa posso fare per te:\n\n"
        "🔴 /live - Mostra le partite in corso (se ce ne sono).\n"
        "📊 /classifica - La classifica aggiornata della Serie A.\n"
        "⚽️ /marcatori - La classifica dei migliori marcatori.\n"
        "🗓 /calendario - Le prossime 5 partite in programma."
    )
    update.message.reply_text(welcome_message)

def live(update: telegram.Update, context: CallbackContext):
    """Mostra i risultati delle partite in corso."""
    update.message.reply_text("⏳ Sto cercando le partite in corso...")
    data = fetch_data(f"competitions/{SERIE_A_ID}/matches?status=LIVE")

    if not data or not data.get('matches'):
        update.message.reply_text("Nessuna partita della Serie A è in corso in questo momento.")
        return

    message = "🔴 **Partite in corso** 🔴\n\n"
    for match in data['matches']:
        home_team = match['homeTeam']['shortName']
        away_team = match['awayTeam']['shortName']
        score_home = match['score']['fullTime']['home']
        score_away = match['score']['fullTime']['away']
        minute = match.get('minute', 'N/D') # Potrebbe non essere sempre presente

        message += f"▪️ {home_team} **{score_home} - {score_away}** {away_team}\n"

    update.message.reply_text(message, parse_mode='Markdown')

def classifica(update: telegram.Update, context: CallbackContext):
    """Mostra la classifica della Serie A."""
    update.message.reply_text("📊 Sto caricando la classifica...")
    data = fetch_data(f"competitions/{SERIE_A_ID}/standings")

    if not data or not data['standings']:
        update.message.reply_text("Impossibile recuperare la classifica al momento.")
        return

    table = data['standings'][0]['table']
    message = "🏆 **Classifica Serie A** 🏆\n\n`Pos Squadra              Pt   G`\n"
    message += "`--------------------------------`\n"
    for team in table:
        pos = str(team['position']).rjust(2)
        name = team['team']['shortName'].ljust(18)
        points = str(team['points']).rjust(3)
        played = str(team['playedGames']).rjust(3)
        message += f"`{pos}. {name} {points} {played}`\n"

    update.message.reply_text(message, parse_mode='Markdown')

def marcatori(update: telegram.Update, context: CallbackContext):
    """Mostra la classifica marcatori."""
    update.message.reply_text("⚽️ Sto caricando la classifica marcatori...")
    data = fetch_data(f"competitions/{SERIE_A_ID}/scorers")

    if not data or not data.get('scorers'):
        update.message.reply_text("Impossibile recuperare la classifica marcatori.")
        return

    message = "🥅 **Classifica Marcatori Serie A** 🥅\n\n"
    for i, scorer in enumerate(data['scorers'][:15], 1): # Mostra i primi 15
        name = scorer['player']['name']
        team = scorer['team']['shortName']
        goals = scorer['goals']
        message += f"*{i}.* {name} (*{team}*) - *{goals}* gol\n"

    update.message.reply_text(message, parse_mode='Markdown')

def calendario(update: telegram.Update, context: CallbackContext):
    """Mostra le prossime partite in calendario."""
    update.message.reply_text("🗓 Sto cercando le prossime partite...")
    data = fetch_data(f"competitions/{SERIE_A_ID}/matches?status=SCHEDULED")

    if not data or not data.get('matches'):
        update.message.reply_text("Non ho trovato prossime partite in programma.")
        return

    message = "📅 **Prossime Partite in Calendario** 📅\n\n"
    for match in data['matches'][:5]: # Mostra le prossime 5
        home_team = match['homeTeam']['shortName']
        away_team = match['awayTeam']['shortName']
        
        # Converte la data UTC in formato italiano (orario di Roma)
        match_date_utc = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
        match_date_local = match_date_utc + timedelta(hours=2) # Da UTC a CEST
        date_str = match_date_local.strftime("%d/%m/%Y ore %H:%M")

        message += f"▪️ *{date_str}*\n   {home_team} vs {away_team}\n\n"
    
    update.message.reply_text(message, parse_mode='Markdown')


def main():
    """Funzione principale per avviare il bot."""
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'IL_TUO_TOKEN_TELEGRAM':
        print("Errore: Il token di Telegram non è stato impostato.")
        return
    if not FOOTBALL_DATA_TOKEN or FOOTBALL_DATA_TOKEN == 'LA_TUA_API_KEY_FOOTBALL_DATA':
        print("Errore: La API key di football-data.org non è stata impostata.")
        return
        
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Registrazione dei comandi
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("live", live))
    dispatcher.add_handler(CommandHandler("classifica", classifica))
    dispatcher.add_handler(CommandHandler("marcatori", marcatori))
    dispatcher.add_handler(CommandHandler("calendario", calendario))

    # Avvio del bot
    updater.start_polling()
    print("Bot avviato e in ascolto...")
    updater.idle()

if __name__ == '__main__':
    main()