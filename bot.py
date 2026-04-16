import requests
import datetime
import os
import random

# Configuration
API_KEY = os.getenv("RIOT_API_KEY")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = "931963091166564382"

GAME_NAME = "AMD LA GRINTA"
TAG_LINE = "6276"
REGION = "europe"
PLATFORM = "euw1"

# --- BANQUE DE PHRASES ---
PHRASES_MATIN = [
    "Debout ! L'évolution n'attend pas les dormeurs.",
    "Le soleil est levé, mais ton winrate est toujours au point mort.",
    "Une nouvelle journée pour prouver que tu n'es pas un simple cobaye.",
    "Analyse matinale : Niveau de grinta proche du néant.",
    "Même mes automates ont plus de réflexes que toi au réveil. Lance une game."
]

PHRASES_SOIR = [
    "Le bilan de la journée est médiocre. Pourquoi n'as-tu pas joué ?",
    "La nuit tombe, et ton historique de match est toujours vide. Décevant.",
    "Encore une journée perdue pour le progrès. Tu recules, AMD.",
    "Mes capteurs indiquent une peur panique de la SoloQ ce soir.",
    "Le Glorieux Évoluteur est irrité par ton manque d'implication."
]

PHRASES_LONGUE_DUREE = [
    "Est-ce que tu te souviens seulement de la touche 'Z' de ton clavier ?",
    "À ce stade, ce n'est plus une pause, c'est une retraite spirituelle.",
    "Ton rang va finir par se transformer en poussière, tout comme tes ambitions."
]

def get_data(url):
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

def main():
    acc = get_data(f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not acc: return
    
    puuid = acc['puuid']
    m_list = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1")
    if not m_list: return

    game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{m_list[0]}")
    rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")

    if game and rank_info is not None:
        last_game_ts = game['info']['gameEndTimestamp'] / 1000
        last_date = datetime.datetime.fromtimestamp(last_game_ts)
        diff = datetime.datetime.now() - last_date
        days = diff.days
        
        # Choix de la phrase aléatoire
        now = datetime.datetime.now()
        if days > 7:
            phrase = random.choice(PHRASES_LONGUE_DUREE)
        elif now.hour < 12:
            phrase = random.choice(PHRASES_MATIN)
        else:
            phrase = random.choice(PHRASES_SOIR)

        solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), {"tier": "UNRANKED", "rank": "", "leaguePoints": 0})

        embed = {
            "content": f"📢 Message pour <@{DISCORD_USER_ID}>",
            "embeds": [{
                "title": f"⚙️ ANALYSE DE VIKTOR",
                "description": f"**{phrase}**\n\nCela fait **{days} jours** sans activité.",
                "color": 0xe67e22,
                "fields": [
                    {"name": "Rang", "value": f"{solo['tier']} {solo['rank']}", "inline": True},
                    {"name": "Dernière game", "value": last_date.strftime('%d/%m/%Y'), "inline": True}
                ],
                "image": {"url": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Viktor_0.jpg"}
            }]
        }
        requests.post(WEBHOOK, json=embed)

if __name__ == "__main__":
    main()
