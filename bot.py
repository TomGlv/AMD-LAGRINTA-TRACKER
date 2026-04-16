import requests
import datetime
import os

# Récupération des variables depuis GitHub Secrets
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

REGION_ROUTE = "europe"
GAME_NAME = "AMD LA GRINTA"
TAG_LINE = "6276"

def run_bot():
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    # 1. Récupérer le PUUID
    acc_url = f"https://{REGION_ROUTE}.api.riotgames.com/riot/account/v1/accounts/by-game-name/{GAME_NAME}/{TAG_LINE}"
    res = requests.get(acc_url, headers=headers)
    if res.status_code != 200: return
    
    puuid = res.json()['puuid']

    # 2. Récupérer le dernier match
    m_url = f"https://{REGION_ROUTE}.api.riotgames.com/lol/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=1"
    res = requests.get(m_url, headers=headers)
    if not res.json(): return
    
    # 3. Détails du match
    last_match_id = res.json()[0]
    d_url = f"https://{REGION_ROUTE}.api.riotgames.com/lol/match/v1/matches/{last_match_id}"
    match_data = requests.get(d_url, headers=headers).json()

    # Calcul du temps (gameEndTimestamp est en ms)
    last_game_ts = match_data['info']['gameEndTimestamp'] / 1000
    days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(last_game_ts)).days

    # Envoi Discord
    msg = f"📅 Jour {days} : Toujours aucun signe de **{GAME_NAME}**. La retraite lui va si bien."
    requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

if __name__ == "__main__":
    run_bot()
