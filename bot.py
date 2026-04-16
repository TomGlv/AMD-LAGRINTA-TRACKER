import requests
import datetime
import os
import time

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
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"⚠️ Erreur API : {res.status_code} sur {url}")
            return None
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return None

def main():
    print(f"🚀 Lancement du check pour {GAME_NAME}#{TAG_LINE}")
    
    # 1. Récupérer le PUUID
    url_acc = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}"
    acc = get_data(url_acc)
    
    if not acc:
        print("❌ Impossible de récupérer le compte. Vérifie le nom ou la clé API.")
        return
    
    puuid = acc['puuid']
    print(f"✅ PUUID récupéré : {puuid[:10]}...")

    # 2. Récupérer le dernier match (tous modes confondus pour éviter le vide)
    url_matches = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1"
    m_list = get_data(url_matches)
    
    if not m_list:
        print("❌ Aucun match trouvé pour ce joueur.")
        return

    match_id = m_list[0]
    print(f"🔍 Analyse du match : {match_id}")

    # 3. Détails du match et Rang
    game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}")
    rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")

    if game and rank_info is not None:
        # Calcul du temps
        last_game_ts = game['info']['gameEndTimestamp'] / 1000
        last_date = datetime.datetime.fromtimestamp(last_game_ts)
        diff = datetime.datetime.now() - last_date
        days = diff.days
        
        # Récupération du rang SoloQ
        solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), {"tier": "UNRANKED", "rank": "", "leaguePoints": 0})

        # Construction du message
        print(f"📤 Envoi du message Discord (Inactivité : {days} jours)")
        embed = {
            "content": f"📢 Rapport du soir pour <@{DISCORD_USER_ID}>",
            "embeds": [{
                "title": f"📉 BILAN D'INACTIVITÉ : {GAME_NAME}",
                "description": f"Cela fait **{days} jours** que tu n'as pas lancé de game sur ce compte.",
                "color": 0xe67e22, # Orange
                "fields": [
                    {"name": "Rang actuel", "value": f"**{solo['tier']} {solo['rank']}** ({solo['leaguePoints']} LP)", "inline": True},
                    {"name": "Dernier match", "value": last_date.strftime('%d/%m/%Y à %H:%M'), "inline": True}
                ],
                "image": {"url": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Viktor_0.jpg"},
                "footer": {"text": "Le Glorieux Évoluteur attend ton retour."}
            }]
        }
        
        r = requests.post(WEBHOOK, json=embed)
        print(f"✨ Statut Discord : {r.status_code}")
    else:
        print("❌ Erreur lors de la récupération des détails de la game ou du rang.")

if __name__ == "__main__":
    main()
