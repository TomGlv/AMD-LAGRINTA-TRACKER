import requests
import datetime
import os

# Configuration
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

REGION_ACCOUNT = "europe"      # Pour le PUUID
REGION_PLATFORM = "euw1"       # Pour le Rang (EUW)
GAME_NAME = "AMD LA GRINTA"
TAG_LINE = "6276"

def run_bot():
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    # 1. Récupérer le PUUID
    acc_url = f"https://{REGION_ACCOUNT}.api.riotgames.com/riot/account/v1/accounts/by-game-name/{GAME_NAME}/{TAG_LINE}"
    res = requests.get(acc_url, headers=headers)
    if res.status_code != 200: return
    data_acc = res.json()
    puuid = data_acc['puuid']

    # 2. Récupérer l'ID d'invocateur (nécessaire pour le rang)
    sum_url = f"https://{REGION_PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    res_sum = requests.get(sum_url, headers=headers)
    summoner_id = res_sum.json()['id']

    # 3. Récupérer le Rang et LPs
    rank_url = f"https://{REGION_PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    rank_data = requests.get(rank_url, headers=headers).json()
    
    rank_str = "Unranked"
    lp = 0
    tier = ""
    
    for entry in rank_data:
        if entry['queueType'] == "RANKED_SOLO_5x5":
            tier = entry['tier'] # Ex: DIAMOND
            rank = entry['rank'] # Ex: II
            lp = entry['leaguePoints']
            rank_str = f"{tier} {rank}"
            break

    # 4. Calcul vers le Master
    # On estime grossièrement la distance. Master = Diamond 1, 100 LP.
    # Si déjà Master, on change le message.
    if tier == "MASTER":
        master_status = "Il est déjà Master, quel crack."
    else:
        # Calcul simplifié : 100 LP par division + les LP manquants
        # Note : C'est une estimation car on ne gère pas toutes les divisions ici
        # On va juste dire combien de wins il faut s'il est en D1 par exemple.
        if tier == "DIAMOND":
            # Si D1, il manque (100 - lp) pour le BO. Si D2, c'est plus.
            # On va rester simple : "À environ X wins du Master"
            needed_lp = 100 - lp 
            if "I" in rank and tier == "DIAMOND":
                wins_needed = int(needed_lp / 20) + (1 if needed_lp % 20 > 0 else 0)
                master_status = f"Plus que environ **{wins_needed} wins** (+20lp/w) pour le Master !"
            else:
                master_status = "Le Master est encore loin, va falloir cliquer."
        else:
            master_status = "Le Master ? On en reparle l'année prochaine."

    # 5. Récupérer le dernier match pour les jours d'inactivité
    m_url = f"https://{REGION_ACCOUNT}.api.riotgames.com/lol/match/v1/matches/by-puuid/{puuid}/ids?start=0&count=1"
    match_ids = requests.get(m_url, headers=headers).json()
    
    days = "?"
    if match_ids:
        d_url = f"https://{REGION_ACCOUNT}.api.riotgames.com/lol/match/v1/matches/{match_ids[0]}"
        match_info = requests.get(d_url, headers=headers).json()
        last_game_ts = match_info['info']['gameEndTimestamp'] / 1000
        days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(last_game_ts)).days

    # 6. Construction de l'Embed Discord (plus joli)
    payload = {
        "embeds": [{
            "title": f"Rapport d'activité : {GAME_NAME} #{TAG_LINE}",
            "color": 15418782, # Rouge/Orange
            "description": f"📅 **Jour {days}** d'inactivité totale.",
            "fields": [
                {"name": "Rang Actuel", "value": f"🏆 {rank_str} ({lp} LP)", "inline": True},
                {"name": "Objectif Master", "value": f"🎯 {master_status}", "inline": False}
            ],
            "image": {
                "url": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Viktor_0.jpg"
            },
            "footer": {"text": "Dernière actualisation via GitHub Actions"}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    run_bot()
