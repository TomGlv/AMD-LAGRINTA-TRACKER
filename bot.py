import requests
import os
import time
import datetime

# --- CONFIGURATION ---
API_KEY = os.getenv("RIOT_API_KEY") # Vérifie bien le nom dans tes GitHub Secrets
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_USER_ID = "931963091166564382"

GAME_NAME = "AMD LA GRINTA"
TAG_LINE = "6276"
REGION = "europe"
PLATFORM = "euw1"
FILE_NAME = "last_match_grinta.txt"

def get_data(url):
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        print(f"Erreur API sur {url} : {res.status_code}")
        return None

def calculate_master_distance(tier, rank, lp):
    if tier == "MASTER": return "Déjà Master !"
    if tier != "DIAMOND": return "Encore loin du Master..."
    
    ranks_value = {"IV": 300, "III": 200, "II": 100, "I": 0}
    lp_to_master = ranks_value.get(rank, 0) + (100 - lp)
    wins_needed = -(-lp_to_master // 20) # Arrondi au supérieur
    return f"{lp_to_master} LP ({wins_needed} net wins)"

def main():
    # 1. Récupérer le PUUID
    acc = get_data(f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not acc: return
    puuid = acc['puuid']

    # 2. Récupérer les derniers matchs (Match-V5)
    m_list = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=3")
    if not m_list: return

    # 3. Gestion de la mémoire (pour ne pas spammer)
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            saved_id = f.read().strip()
    else:
        saved_id = ""

    m_list.reverse() # Pour traiter du plus vieux au plus récent
    new_last_id = saved_id
    found_new = False

    for match_id in m_list:
        if match_id == saved_id: continue 

        # 4. Récupérer les détails du match et du rang
        game = get_data(f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}")
        rank_info = get_data(f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")

        if game and rank_info:
            found_new = True
            p = next(pl for pl in game['info']['participants'] if pl['puuid'] == puuid)
            solo = next((i for i in rank_info if i['queueType'] == "RANKED_SOLO_5x5"), {"tier": "UNRANKED", "rank": "", "leaguePoints": 0})
            
            # Calculs
            dist_master = calculate_master_distance(solo['tier'], solo['rank'], solo['leaguePoints'])
            duration = game['info']['gameDuration']
            last_game_date = datetime.datetime.fromtimestamp(game['info']['gameEndTimestamp'] / 1000)
            days_ago = (datetime.datetime.now() - last_game_date).days

            # Embed Discord
            embed = {
                "content": f"Hé <@{DISCORD_USER_ID}>, le Glorieux Évoluteur te surveille ! 📢",
                "embeds": [{
                    "author": {"name": f"ANALYSE DE GAME | {GAME_NAME}", "icon_url": "https://ddragon.leagueoflegends.com/cdn/14.7.1/img/champion/Viktor.png"},
                    "title": f"{'🟩 VICTOIRE' if p['win'] else '🟥 DÉFAITE'} - {int(duration//60)}m",
                    "description": f"Dernière game jouée il y a **{days_ago} jours**.",
                    "color": 0x2ecc71 if p['win'] else 0xe74c3c,
                    "thumbnail": {"url": f"https://ddragon.leagueoflegends.com/cdn/14.7.1/img/champion/{p['championName']}.png"},
                    "fields": [
                        {"name": "🏆 RANG", "value": f"{solo['tier']} {solo['rank']} ({solo['leaguePoints']} LP)", "inline": True},
                        {"name": "🎯 VERS LE MASTER", "value": dist_master, "inline": True},
                        {"name": "⚔️ KDA", "value": f"{p['kills']}/{p['deaths']}/{p['assists']}", "inline": True},
                        {"name": "🤖 CHAMPION", "value": p['championName'], "inline": True}
                    ],
                    "image": {"url": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Viktor_0.jpg"},
                    "footer": {"text": f"Match ID: {match_id}"},
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                }]
            }

            if requests.post(WEBHOOK, json=embed).status_code in [200, 204]:
                new_last_id = match_id
                time.sleep(2)

    # Sauvegarder le dernier match
    if found_new:
        with open(FILE_NAME, "w") as f:
            f.write(new_last_id)
        print(f"Mémoire mise à jour : {new_last_id}")

if __name__ == "__main__":
    main()
