import os
import requests
from supabase import create_client, Client
from datetime import datetime

# 1. Puxa as credenciais seguras do GitHub Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Novas URLs corretas da API (Separadas por equipas e jogos)
URL_EQUIPAS = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/main/football.teams.json"
URL_JOGOS = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/main/football.matches.json"

traducao_paises = {
    "Brazil": "Brasil", "Germany": "Alemanha", "Spain": "Espanha",
    "France": "França", "England": "Inglaterra", "Argentina": "Argentina"
}

traducao_status = {
    "Scheduled": "Agendado", "In Play": "Em Andamento", "Finished": "Encerrado"
}

# Proteção para garantir que números são lidos corretamente
def tratar_numero(valor):
    try:
        if valor and str(valor).strip():
            return int(valor)
    except:
        pass
    return None

def executar_atualizacao():
    print(f"[{datetime.now()}] Iniciando sincronização...")
    try:
        # Atualizar Seleções
        print("A descarregar equipas...")
        resp_equipas = requests.get(URL_EQUIPAS)
        resp_equipas.raise_for_status()
        
        for equipa in resp_equipas.json():
            nome_en = equipa.get('name_en', '')
            
            dados_equipa = {
                "id": tratar_numero(equipa.get('id')), 
                "nome_original": nome_en, 
                "nome_ptbr": traducao_paises.get(nome_en, nome_en),
                "codigo_fifa": equipa.get('fifa_code', ''), 
                "grupo": equipa.get('groups', ''),
                "bandeira_url": equipa.get('flag', '')
            }
            if dados_equipa["id"] is not None:
                supabase.table("selecoes").upsert(dados_equipa).execute()
                
        # Atualizar Jogos
        print("A descarregar jogos...")
        resp_jogos = requests.get(URL_JOGOS)
        resp_jogos.raise_for_status()
        
        for jogo in resp_jogos.json():
            status_original = jogo.get('status', 'Scheduled')
            
            dados_jogo = {
                "id": tratar_numero(jogo.get('id')), 
                "data_hora": jogo.get('date', jogo.get('local_date')),
                "fase": jogo.get('matchday', 'Fase de Grupos'),
                "time_casa_id": tratar_numero(jogo.get('home_team_id')),
                "time_visitante_id": tratar_numero(jogo.get('away_team_id')),
                "gols_casa": tratar_numero(jogo.get('home_score')),
                "gols_visitante": tratar_numero(jogo.get('away_score')),
                "status": traducao_status.get(status_original, status_original)
            }
            if dados_jogo["id"] is not None:
                supabase.table("jogos").upsert(dados_jogo).execute()

        # Atualizar Carimbo de tempo
        supabase.table("status_sistema").upsert({"id": 1, "ultima_atualizacao": "now()"}).execute()
        print("Sincronização concluída com sucesso no Supabase!")

    except Exception as e:
        print(f"Erro durante a atualização: {e}")

if __name__ == "__main__":
    executar_atualizacao()
