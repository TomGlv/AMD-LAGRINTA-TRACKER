import requests
import datetime
import os

# Configuration
API_KEY = os.getenv("RIOT_API_KEY")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = "931963091166564382"

GAME_NAME = "AMD LA GRINTA"
TAG_LINE = "6276"
REGION = "europe"
PLATFORM = "euw1"

def get_data(url):
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

def main():
    # 1. Récupérer le PUUID
    acc = get_data(f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not acc: 
        print("Erreur : Compte introuvable")
        return
    puuid = acc['puuid']

    # 2. Récupérer le dernier match
    m_list = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1")
    if not m_list: return

    game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{m_list[0]}")
    rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")

    if game and rank_info:
        # Calcul du temps écoulé
        last_game_ts = game['info']['gameEndTimestamp'] / 1000
        last_date = datetime.datetime.fromtimestamp(last_game_ts)
        diff = datetime.datetime.now() - last_date
        days = diff.days
        
        # Récupération du rang
        solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), {"tier": "UNRANKED", "rank": "", "leaguePoints": 0})

        # Message
        embed = {
            "content": f"📢 Rappel quotidien pour <@{DISCORD_USER_ID}>",
            "embeds": [{
                "title": f"BILAN D'INACTIVITÉ : {GAME_NAME}",
                "description": f"Cela fait **{days} jours** que tu n'as pas lancé de ranked.",
                "color": 0x3498db,
                "fields": [
                    {"name": "Rang actuel", "value": f"{solo['tier']} {solo['rank']} ({solo['leaguePoints']} LP)", "inline": True},
                    {"name": "Dernière game", "value": last_date.strftime('%d/%m/%Y'), "inline": True}
                ],
                "image": {"url": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Viktor_0.jpg"},
                "footer": {"text": "Le Glorieux Évoluteur ne tolère pas la paresse."}
            }]
        }
        requests.post(WEBHOOK, json=embed)

if __name__ == "__main__":
    main()
