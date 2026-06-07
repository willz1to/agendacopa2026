import requests
from supabase import create_client, Client
from datetime import datetime

# 1. Credenciais do Supabase (Substitua pelas suas)
SUPABASE_URL = "SUA_URL_AQUI"
SUPABASE_KEY = "SUA_CHAVE_ANON_AQUI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# URL bruta da API no GitHub (adapte conforme o caminho exato do JSON do repositório)
GITHUB_API_URL = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/master/data.json"

# 2. Dicionários de Tradução Rápida (Mapeamento)
traducao_paises = {
    "Brazil": "Brasil",
    "Germany": "Alemanha",
    "Spain": "Espanha",
    "France": "França",
    "England": "Inglaterra",
    "Argentina": "Argentina"
    # Adicione os demais países conforme necessário
}

traducao_status = {
    "Scheduled": "Agendado",
    "In Play": "Em Andamento",
    "Finished": "Encerrado"
}

def executar_atualizacao():
    print(f"[{datetime.now()}] Iniciando sincronização com a API...")
    
    try:
        # Puxa os dados brutos da API
        resposta = requests.get(GITHUB_API_URL)
        resposta.raise_for_status()
        dados_api = resposta.json()
        
        # 3. Processar e Atualizar as Seleções
        # Assumindo que a API tenha um array chamado 'teams'
        if 'teams' in dados_api:
            for time in dados_api['teams']:
                nome_en = time.get('name_en', '')
                
                # Se o país estiver no dicionário, traduz. Se não, usa o original para não quebrar.
                nome_pt = traducao_paises.get(nome_en, nome_en)
                
                dados_time = {
                    "id": time['id'],
                    "nome_original": nome_en,
                    "nome_ptbr": nome_pt,
                    "codigo_fifa": time.get('fifa_code', ''),
                    "grupo": time.get('groups', ''),
                    "bandeira_url": time.get('flag', '')
                }
                
                # O upsert atualiza o registro se o ID já existir, ou insere um novo
                supabase.table("selecoes").upsert(dados_time).execute()
                
        # 4. Processar e Atualizar os Jogos
        # Assumindo que a API tenha um array chamado 'matches'
        if 'matches' in dados_api:
            for jogo in dados_api['matches']:
                status_original = jogo.get('status', 'Scheduled')
                status_pt = traducao_status.get(status_original, status_original)
                
                dados_jogo = {
                    "id": jogo['id'],
                    "data_hora": jogo['date'], # O formato precisa ser reconhecido pelo banco (ex: ISO 8601)
                    "fase": jogo.get('matchday', 'Fase de Grupos'),
                    "time_casa_id": jogo.get('home_team_id'),
                    "time_visitante_id": jogo.get('away_team_id'),
                    "gols_casa": jogo.get('home_score'),
                    "gols_visitante": jogo.get('away_score'),
                    "status": status_pt
                }
                
                supabase.table("jogos").upsert(dados_jogo).execute()

        # 5. Atualizar o Carimbo de Tempo (Para a "bolinha verde" no front-end)
        supabase.table("status_sistema").upsert({
            "id": 1,
            "ultima_atualizacao": "now()"
        }).execute()
        
        print("Sincronização concluída com sucesso no Supabase!")

    except Exception as e:
        print(f"Erro durante a atualização: {e}")

if __name__ == "__main__":
    executar_atualizacao()
