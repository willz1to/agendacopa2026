import os
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta

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

def executar_atualizacao():
    print(f"[{datetime.now()}] Iniciando sincronização...")
    try:
        resp_equipas = requests.get(URL_EQUIPAS)
        resp_equipas.raise_for_status()
        equipas_map = {}
        
        for equipa in resp_equipas.json():
            id_eq = tratar_id(equipa.get('id'))
            if id_eq:
                nome_en = equipa.get('name_en', '')
                nome_pt = traducao_paises.get(nome_en, nome_en)
                codigo_fifa = equipa.get('fifa_code', '')
                
                equipas_map[id_eq] = {
                    "nome": nome_pt,
                    "codigo": codigo_fifa
                }
                
                dados_equipa = {
                    "id": id_eq, "nome_original": nome_en, "nome_ptbr": nome_pt,
                    "codigo_fifa": codigo_fifa, "grupo": equipa.get('groups', ''),
                    "bandeira_url": equipa.get('flag', '')
                }
                supabase.table("selecoes").upsert(dados_equipa).execute()
                
        resp_jogos = requests.get(URL_JOGOS)
        resp_jogos.raise_for_status()
        jogos_lista = resp_jogos.json()
        
        for jogo in jogos_lista:
            id_jg = tratar_id(jogo.get('id'))
            if id_jg:
                status_original = jogo.get('status', 'Scheduled')
                status_pt = traducao_status.get(status_original, status_original)
                dados_jogo = {
                    "id": id_jg, "data_hora": jogo.get('date', jogo.get('local_date')),
                    "fase": jogo.get('matchday', 'Fase de Grupos'),
                    "time_casa_id": tratar_id(jogo.get('home_team_id')),
                    "time_visitante_id": tratar_id(jogo.get('away_team_id')),
                    "gols_casa": tratar_gols(jogo.get('home_score')),
                    "gols_visitante": tratar_gols(jogo.get('away_score')),
                    "status": status_pt
                }
                supabase.table("jogos").upsert(dados_jogo).execute()

        supabase.table("status_sistema").upsert({"id": 1, "ultima_atualizacao": "now()"}).execute()
        print("Supabase atualizado!")

        # GERAÇÃO DO CALENDÁRIO ESTÁTICO .ICS (Agora usando Siglas FIFA em vez de Emojis)
        print("Gerando ficheiro de calendário .ics...")
        ics_linhas = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Copa2026//Calendario Estatico//PT",
            "X-WR-CALNAME:Copa do Mundo 2026",
            "X-WR-TIMEZONE:UTC",
            "REFRESH-INTERVAL;VALUE=DURATION:PT15M",
            "X-PUBLISHED-TTL:PT15M"
        ]

        for jogo in jogos_lista:
            id_jg = tratar_id(jogo.get('id'))
            if not id_jg: continue
            
            id_casa = tratar_id(jogo.get('home_team_id'))
            id_fora = tratar_id(jogo.get('away_team_id'))
            
            casa = equipas_map.get(id_casa, {"nome": "A Definir", "codigo": ""}) if id_casa else {"nome": "A Definir", "codigo": ""}
            fora = equipas_map.get(id_fora, {"nome": "A Definir", "codigo": ""}) if id_fora else {"nome": "A Definir", "codigo": ""}
            
            sigla_casa = f"[{casa['codigo']}] " if casa['codigo'] else ""
            sigla_fora = f" [{fora['codigo']}]" if fora['codigo'] else ""
            
            status_original = jogo.get('status', 'Scheduled')
            status_pt = traducao_status.get(status_original, status_original)
            g_casa = tratar_gols(jogo.get('home_score'))
            g_fora = tratar_gols(jogo.get('away_score'))

            if status_pt in ["Em Andamento", "Encerrado"] and g_casa is not None and g_fora is not None:
                titulo = f"{sigla_casa}{casa['nome']} {g_casa} x {g_fora} {fora['nome']}{sigla_fora} ({status_pt})"
            else:
                titulo = f"{sigla_casa}{casa['nome']} x {fora['nome']}{sigla_fora}"

            data_raw = jogo.get('date', jogo.get('local_date'))
            try:
                dt_limpa = data_raw.replace("Z", "").replace("T", " ").split(".")[0]
                dt_obj = datetime.strptime(dt_limpa, "%Y-%m-%d %H:%M:%S")
                dt_start = dt_obj.strftime("%Y%m%dT%H%M%SZ")
                dt_end = (dt_obj + timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
            except: continue

            ics_linhas.extend([
                "BEGIN:VEVENT",
                f"UID:jogo_2026_{id_jg}",
                f"DTSTART:{dt_start}",
                f"DTEND:{dt_end}",
                f"SUMMARY:{titulo}",
                f"DESCRIPTION:Fase: {jogo.get('matchday', 'Fase de Grupos')}\\nEstado: {status_pt}",
                "LOCATION:Estádio da Partida",
                "END:VEVENT"
            ])

        ics_linhas.append("END:VCALENDAR")
        
        with open("calendario.ics", "w", encoding="utf-8") as f:
            f.write("\r\n".join(ics_linhas))
        print("Ficheiro calendario.ics gerado com sucesso!")

    except Exception as e: print(f"Erro durante a atualização: {e}")

if __name__ == "__main__": executar_atualizacao()
    
