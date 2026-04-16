import requests
import datetime
import os

# Configuration (récupérée via GitHub Secrets pour la sécurité)
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# L'ID Discord que tu as fourni pour le ping
DISCORD_USER_ID = "931963091166564382"

REGION_ACCOUNT = "europe"
REGION_PLATFORM = "euw1"
GAME_NAME = "AMD LA GRINTA"
TAG_LINE = "6276"

def run_bot():
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    # 1. Récupérer le PUUID via Riot ID
    acc_url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-game-name/{GAME_NAME}/{TAG_LINE}"
    res = requests.get(acc_url, headers=headers)
    if res.status_code != 200:
        print(f"Erreur Account API: {res.status_code}")
        return
    puuid = res.json()['puuid']

    # 2. Récupérer l'ID d'invocateur (Summoner ID)
    sum_url = f"https://{REGION_PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    res_sum = requests.get(sum_url, headers=headers)
    summoner_id = res_sum.json()['id']

    # 3. Récupérer le Rang et les LPs
    rank_url = f"https://{REGION_PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    rank_data = requests.get(rank_url, headers=headers).json()
    
    rank_str, lp, tier, division = "Unranked", 0, "", ""
    for entry in rank_data:
        if entry['queueType'] == "RANKED_SOLO_5x5":
            tier, division, lp = entry['tier'], entry['rank'], entry['leaguePoints']
            rank_str = f"{tier} {division}"
            break

    # 4. Calcul précis du chemin vers le Master (D1 100 LP)
    if tier == "MASTER" or tier == "GRANDMASTER" or tier == "CHALLENGER":
        master_status = "Déjà Master ou plus. C'est un monstre."
    elif tier == "DIAMOND":
        # Valeur des divisions pour le calcul (en LP)
        div_value = {"I": 0, "II": 100, "III": 200, "IV": 300}
        points_to_master = div_value.get(division, 0) + (100 - lp)
        # Estimation à 20 LP par victoire
        wins = int(points_to_master / 20) + (1 if points_to_master % 20 > 0 else 0)
        master_status = f"Encore environ **{wins} wins** (+20lp/w) pour le Master !"
    else:
        master_status = "Le Master est un rêve lointain pour l'instant..."

    # 5. Calcul des jours d'inactivité (Dernier match)
    m_url = f"https://{REGION_ACCOUNT}.api.riotgames.com/lol/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=1"
    match_ids = requests.get(m_url, headers=headers).json()
    
    days = "?"
    if match_ids:
        d_url = f"https://{REGION_ACCOUNT}.api.riotgames.com/lol/match/v1/matches/{match_ids[0]}"
        m_info = requests.get(d_url, headers=headers).json()
        # gameEndTimestamp est en millisecondes
        last_game_ts = m_info['info']['gameEndTimestamp'] / 1000
        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(last_game_ts)
        days = delta.days

    # 6. Envoi du Webhook avec le Ping et l'image de Viktor
    payload = {
        "content": f"Hé <@{DISCORD_USER_ID}>, va falloir cliquer un peu ! 📢",
        "embeds": [{
            "title": f"Rapport d'activité : {GAME_NAME} #{TAG_LINE}",
            "description": f"Dernière game jouée il y a **{days} jours**.",
            "color": 15418782, # Couleur orange/rouge
            "fields": [
                {"name": "Rang actuel", "value": f"🏆 {rank_str} ({lp} LP)", "inline": True},
                {"name": "Route vers le Master", "value": f"🎯 {master_status}", "inline": False}
            ],
            "image": {
                "url": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Viktor_0.jpg"
            },
            "footer": {"text": "Dernière mise à jour : Viktor Bot"}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    run_bot()
