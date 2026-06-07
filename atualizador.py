import os
import requests
from supabase import create_client, Client
from datetime import datetime

# 1. Puxa as credenciais seguras do GitHub Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# URL da API
GITHUB_API_URL = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/master/data.json"

# 2. Dicionários de Tradução
traducao_paises = {
    "Brazil": "Brasil", "Germany": "Alemanha", "Spain": "Espanha",
    "France": "França", "England": "Inglaterra", "Argentina": "Argentina"
}

traducao_status = {
    "Scheduled": "Agendado", "In Play": "Em Andamento", "Finished": "Encerrado"
}

def executar_atualizacao():
    print(f"[{datetime.now()}] Iniciando sincronização...")
    try:
        resposta = requests.get(GITHUB_API_URL)
        resposta.raise_for_status()
        dados_api = resposta.json()
        
        # Atualizar Seleções
        if 'teams' in dados_api:
            for time in dados_api['teams']:
                nome_en = time.get('name_en', '')
                nome_pt = traducao_paises.get(nome_en, nome_en)
                
                dados_time = {
                    "id": time['id'], "nome_original": nome_en, "nome_ptbr": nome_pt,
                    "codigo_fifa": time.get('fifa_code', ''), "grupo": time.get('groups', ''),
                    "bandeira_url": time.get('flag', '')
                }
                supabase.table("selecoes").upsert(dados_time).execute()
                
        # Atualizar Jogos
        if 'matches' in dados_api:
            for jogo in dados_api['matches']:
                status_original = jogo.get('status', 'Scheduled')
                status_pt = traducao_status.get(status_original, status_original)
                
                dados_jogo = {
                    "id": jogo['id'], "data_hora": jogo['date'],
                    "fase": jogo.get('matchday', 'Fase de Grupos'),
                    "time_casa_id": jogo.get('home_team_id'),
                    "time_visitante_id": jogo.get('away_team_id'),
                    "gols_casa": jogo.get('home_score'),
                    "gols_visitante": jogo.get('away_score'),
                    "status": status_pt
                }
                supabase.table("jogos").upsert(dados_jogo).execute()

        # Atualizar Status (Carimbo de tempo)
        supabase.table("status_sistema").upsert({"id": 1, "ultima_atualizacao": "now()"}).execute()
        print("Sincronização concluída com sucesso no Supabase!")

    except Exception as e:
        print(f"Erro durante a atualização: {e}")

if __name__ == "__main__":
    executar_atualizacao()
