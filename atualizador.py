import os
import requests
from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

URL_EQUIPAS = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/main/football.teams.json"
URL_JOGOS = "https://raw.githubusercontent.com/rezarahiminia/worldcup2026/main/football.matches.json"

traducao_paises = {
    "Brazil": "Brasil", "Germany": "Alemanha", "Spain": "Espanha",
    "France": "França", "England": "Inglaterra", "Argentina": "Argentina",
    "Portugal": "Portugal", "Netherlands": "Países Baixos", "Belgium": "Bélgica",
    "Croatia": "Croácia", "Italy": "Itália", "Uruguay": "Uruguai", "Colombia": "Colômbia", 
    "Mexico": "México", "United States": "Estados Unidos", "Canada": "Canadá", 
    "Morocco": "Marrocos", "Senegal": "Senegal", "Japan": "Japão", "South Korea": "Coreia do Sul", 
    "Australia": "Austrália", "Iran": "Irã", "Saudi Arabia": "Arábia Saudita", "Ecuador": "Equador",
    "Switzerland": "Suíça", "Denmark": "Dinamarca", "Serbia": "Sérvia", "Poland": "Polônia", 
    "Tunisia": "Tunísia", "Cameroon": "Camarões", "Ghana": "Gana", "Costa Rica": "Costa Rica", 
    "Ukraine": "Ucrânia", "Peru": "Peru", "Chile": "Chile", "Sweden": "Suécia", "Norway": "Noruega",
    "Austria": "Áustria", "Turkey": "Turquia", "Egypt": "Egito", "Algeria": "Argélia", 
    "Nigeria": "Nigéria", "Ivory Coast": "Costa do Marfim", "South Africa": "África do Sul", 
    "New Zealand": "Nova Zelândia", "Venezuela": "Venezuela", "Paraguay": "Paraguai", 
    "Bolivia": "Bolívia", "Qatar": "Catar", "Panama": "Panamá", "Jamaica": "Jamaica"
}
traducao_status = { "Scheduled": "Agendado", "In Play": "Em Andamento", "Finished": "Encerrado" }

def tratar_id(valor):
    try: return int(valor) if int(valor) > 0 else None
    except: return None

def tratar_gols(valor):
    try: return int(valor) if valor is not None and str(valor).strip() != "" else None
    except: return None

# Função para traduzir "1st Group A" para "1º Grupo A"
def formatar_placeholder(jogo, prefixo):
    nome = jogo.get(f'{prefixo}_team_en') or jogo.get(f'{prefixo}_team_name')
    if not nome and isinstance(jogo.get(f'{prefixo}_team'), dict):
        nome = jogo[f'{prefixo}_team'].get('name_en') or jogo[f'{prefixo}_team'].get('name')
    if not nome: return 'A Definir'
    
    t = str(nome)
    t = t.replace("1st Group", "1º Grupo").replace("2nd Group", "2º Grupo").replace("3rd Group", "3º Grupo")
    t = t.replace("Winner Match", "Venc. Jogo").replace("Runner-up Group", "2º Grupo")
    return t

def executar_atualizacao():
    print(f"[{datetime.now()}] Iniciando sincronização...")
    try:
        resp_equipas = requests.get(URL_EQUIPAS)
        resp_equipas.raise_for_status()
        for equipa in resp_equipas.json():
            nome_en = equipa.get('name_en', '')
            dados_equipa = {
                "id": tratar_id(equipa.get('id')), 
                "nome_original": nome_en, 
                "nome_ptbr": traducao_paises.get(nome_en, nome_en),
                "codigo_fifa": equipa.get('fifa_code', ''), 
                "grupo": equipa.get('groups', ''),
                "bandeira_url": equipa.get('flag', '')
            }
            if dados_equipa["id"] is not None:
                supabase.table("selecoes").upsert(dados_equipa).execute()
                
        resp_jogos = requests.get(URL_JOGOS)
        resp_jogos.raise_for_status()
        for jogo in resp_jogos.json():
            status_original = jogo.get('status', 'Scheduled')
            dados_jogo = {
                "id": tratar_id(jogo.get('id')), 
                "data_hora": jogo.get('date', jogo.get('local_date')),
                "fase": jogo.get('matchday', 'Fase de Grupos'),
                "time_casa_id": tratar_id(jogo.get('home_team_id')),
                "time_visitante_id": tratar_id(jogo.get('away_team_id')),
                "gols_casa": tratar_gols(jogo.get('home_score')),
                "gols_visitante": tratar_gols(jogo.get('away_score')),
                "status": traducao_status.get(status_original, status_original),
                "desc_casa": formatar_placeholder(jogo, 'home'),
                "desc_visitante": formatar_placeholder(jogo, 'away')
            }
            if dados_jogo["id"] is not None:
                supabase.table("jogos").upsert(dados_jogo).execute()

        supabase.table("status_sistema").upsert({"id": 1, "ultima_atualizacao": "now()"}).execute()
        print("Sincronização concluída com sucesso no Supabase!")

    except Exception as e: print(f"Erro durante a atualização: {e}")

if __name__ == "__main__": executar_atualizacao()
