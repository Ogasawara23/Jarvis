# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║         J.A.R.V.I.S  —  MÓDULO DE CLIMA  v2.0                             ║
# ║  Clima atual • Previsão 5 dias • Detecção por IP • Integração total        ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  pip install requests                                                        ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  APIs utilizadas:                                                            ║
# ║  • OpenWeatherMap → clima atual e previsão (gratuito, 1000 req/dia)         ║
# ║  • ip-api.com     → detecta cidade pelo IP (gratuito, sem chave)            ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║  Como usar:                                                                  ║
# ║  1. Coloque sua API KEY em OWM_API_KEY abaixo                               ║
# ║  2. Importe no jarvis_v8.py:  from jarvis_clima import cmd_clima            ║
# ║  3. Chame:  cmd_clima("como está o clima?", ui)                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import requests
import datetime
import time
import json
import os
import tempfile
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════════
# ⚙️  CONFIGURAÇÕES  —  EDITE AQUI
# ══════════════════════════════════════════════════════════════════════════════

# 🔑 Sua chave da OpenWeatherMap
#    Crie grátis em: https://openweathermap.org/api
OWM_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "aa3caf9cba68162effcfa529a3c21342")

# 🏙️  Cidade padrão (usada se a detecção por IP falhar)
CIDADE_PADRAO = "Curitiba"
PAIS_PADRAO   = "BR"

# 🌡️  Unidade de temperatura
#    "metric"   → Celsius   (padrão Brasil)
#    "imperial" → Fahrenheit
#    "standard" → Kelvin
UNIDADE = "metric"

# 🌍  Idioma das descrições do clima
#    "pt_br" → Português Brasil
#    "en"    → Inglês
IDIOMA = "pt_br"

# ⏱️  Tempo máximo para aguardar resposta da API (segundos)
TIMEOUT = 8

# 💾  Cache: evita chamar a API repetidamente
#    Salva o resultado por N segundos antes de buscar de novo
CACHE_SEGUNDOS = 600  # 10 minutos

# 📁  Arquivo de cache (salvo na pasta temporária do sistema)
CACHE_FILE = Path(os.path.join(tempfile.gettempdir(), "jarvis_clima_cache.json"))


# ══════════════════════════════════════════════════════════════════════════════
# 🔗  URLs DA API
# ══════════════════════════════════════════════════════════════════════════════

URL_CLIMA_ATUAL = "https://api.openweathermap.org/data/2.5/weather"
URL_PREVISAO    = "https://api.openweathermap.org/data/2.5/forecast"
URL_IP_DETECT   = "http://ip-api.com/json/"


# ══════════════════════════════════════════════════════════════════════════════
# 📚  DICIONÁRIOS DE TRADUÇÃO
# ══════════════════════════════════════════════════════════════════════════════

# Tradução dos dias da semana (API retorna em inglês)
DIAS_SEMANA_PT = {
    "Monday":    "segunda-feira",
    "Tuesday":   "terça-feira",
    "Wednesday": "quarta-feira",
    "Thursday":  "quinta-feira",
    "Friday":    "sexta-feira",
    "Saturday":  "sábado",
    "Sunday":    "domingo",
}

# Mapeamento de ícones de clima para emojis
ICONES_CLIMA = {
    "01": "☀️",   # céu limpo
    "02": "🌤️",  # poucas nuvens
    "03": "☁️",   # nuvens dispersas
    "04": "☁️",   # nublado
    "09": "🌧️",  # chuva leve
    "10": "🌦️",  # chuva
    "11": "⛈️",  # tempestade
    "13": "❄️",   # neve
    "50": "🌫️",  # névoa
}

# Palavras-chave que ativam o comando de clima
PALAVRAS_CLIMA = [
    "clima", "tempo", "temperatura", "previsão", "previsao",
    "chuva", "sol", "frio", "calor", "vento", "umidade",
    "vai chover", "tá chovendo", "está chovendo", "tá frio",
    "está frio", "tá quente", "está quente", "nevar", "neve",
    "como está o tempo", "como tá o tempo", "como tá o clima",
    "como está o clima", "meteorologia", "graus", "celsius",
    "weather", "forecast",
]


# ══════════════════════════════════════════════════════════════════════════════
# 💾  SISTEMA DE CACHE
# ══════════════════════════════════════════════════════════════════════════════

def _salvar_cache(dados: dict, chave: str = "clima_atual") -> None:
    """
    Salva os dados do clima em arquivo JSON local.
    Evita chamadas desnecessárias à API.

    Parâmetros:
        dados  → Dicionário com dados do clima
        chave  → Identificador do cache (ex: "clima_Curitiba")
    """
    try:
        # Carrega cache existente ou cria novo
        cache = {}
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

        # Adiciona timestamp e salva
        cache[chave] = {
            "dados":     dados,
            "timestamp": time.time()
        }

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    except Exception as e:
        # Cache falhou? Sem problema, só continua sem ele
        print(f"[Clima] Aviso: não foi possível salvar cache: {e}")


def _carregar_cache(chave: str = "clima_atual") -> dict | None:
    """
    Carrega dados do cache se ainda estiverem válidos (dentro do CACHE_SEGUNDOS).

    Retorna:
        Dicionário com dados do clima, ou None se cache expirado/inexistente.
    """
    try:
        if not CACHE_FILE.exists():
            return None

        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)

        if chave not in cache:
            return None

        entrada = cache[chave]
        idade   = time.time() - entrada["timestamp"]

        if idade < CACHE_SEGUNDOS:
            print(f"[Clima] ✅ Usando cache ({int(idade)}s atrás)")
            return entrada["dados"]
        else:
            print(f"[Clima] Cache expirado ({int(idade)}s), buscando dados frescos…")
            return None

    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 📡  DETECÇÃO AUTOMÁTICA DE CIDADE POR IP
# ══════════════════════════════════════════════════════════════════════════════

def detectar_cidade_por_ip() -> dict | None:
    """
    Detecta a cidade do usuário automaticamente pelo endereço IP público.
    Usa o serviço ip-api.com (gratuito, sem chave necessária).

    Retorna:
        {
            "cidade": "Curitiba",
            "pais":   "BR",
            "lat":    -25.43,
            "lon":    -49.27,
            "regiao": "Paraná"
        }
        Ou None se a detecção falhar.

    Limitações:
        - Detecta a cidade do provedor de internet, não GPS
        - Pode ser impreciso em conexões via VPN
        - Limite de 45 req/minuto (mais que suficiente)
    """
    try:
        resposta = requests.get(
            URL_IP_DETECT,
            params={
                "fields": "status,message,city,regionName,countryCode,lat,lon"
            },
            timeout=TIMEOUT
        )

        dados = resposta.json()

        # Verifica se a API retornou sucesso
        if dados.get("status") == "success":
            return {
                "cidade": dados.get("city", CIDADE_PADRAO),
                "pais":   dados.get("countryCode", PAIS_PADRAO),
                "lat":    dados.get("lat", 0),
                "lon":    dados.get("lon", 0),
                "regiao": dados.get("regionName", ""),
            }
        else:
            # API retornou erro (ex: IP privado, VPN)
            msg = dados.get("message", "desconhecido")
            print(f"[Clima] ip-api.com retornou: {msg}")
            return None

    except requests.exceptions.ConnectionError:
        print("[Clima] Sem internet para detectar cidade por IP.")
        return None
    except requests.exceptions.Timeout:
        print("[Clima] Timeout ao detectar cidade por IP.")
        return None
    except Exception as e:
        print(f"[Clima] Erro inesperado na detecção por IP: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# ☁️  BUSCA DO CLIMA ATUAL
# ══════════════════════════════════════════════════════════════════════════════

def buscar_clima_atual(cidade: str = None, pais: str = None, forcar_refresh: bool = False) -> dict | None:
    """
    Busca o clima atual de uma cidade na API OpenWeatherMap.

    Parâmetros:
        cidade         → Nome da cidade. Se None, detecta por IP.
        pais           → Código do país (ex: "BR"). Melhora precisão.
        forcar_refresh → Se True, ignora o cache e busca dados novos.

    Retorna dicionário com todos os dados do clima, ou None se falhar.

    Exemplo de retorno:
        {
            "cidade":           "Curitiba",
            "pais":             "BR",
            "temperatura":      18.5,
            "sensacao_termica": 17.2,
            "temp_min":         14.0,
            "temp_max":         22.0,
            "umidade":          72,
            "descricao":        "nuvens dispersas",
            "emoji":            "🌤️",
            "vento_kmh":        14.4,
            "visibilidade_km":  10.0,
            "nascer_sol":       "06:12",
            "por_sol":          "18:34",
            "nuvens_pct":       40,
            "timestamp":        "05/05/2025 às 14:30",
            "fonte_cidade":     "ip"   # ou "manual" ou "padrao"
        }
    """

    # ── Passo 1: Determinar a cidade ──────────────────────────────────────────
    fonte_cidade = "manual"

    if not cidade:
        # Tenta detectar pelo IP primeiro
        print("[Clima] Cidade não informada, detectando por IP…")
        local = detectar_cidade_por_ip()

        if local:
            cidade       = local["cidade"]
            pais         = local["pais"]
            fonte_cidade = "ip"
            print(f"[Clima] Cidade detectada: {cidade}, {pais} ({local['regiao']})")
        else:
            # Fallback: usa cidade padrão das configurações
            cidade       = CIDADE_PADRAO
            pais         = PAIS_PADRAO
            fonte_cidade = "padrao"
            print(f"[Clima] Usando cidade padrão: {cidade}, {pais}")

    # ── Passo 2: Verificar cache ───────────────────────────────────────────────
    chave_cache = f"clima_{cidade}_{pais}".lower().replace(" ", "_")

    if not forcar_refresh:
        dados_cache = _carregar_cache(chave_cache)
        if dados_cache:
            return dados_cache

    # ── Passo 3: Chamar a API ─────────────────────────────────────────────────
    local_query = f"{cidade},{pais}" if pais else cidade

    parametros = {
        "q":     local_query,
        "appid": OWM_API_KEY,
        "units": UNIDADE,
        "lang":  IDIOMA,
    }

    print(f"[Clima] Consultando API para: {local_query}")

    try:
        resposta = requests.get(URL_CLIMA_ATUAL, params=parametros, timeout=TIMEOUT)

        # ── Passo 4: Tratar erros HTTP ────────────────────────────────────────
        if resposta.status_code == 401:
            print("[Clima] ❌ ERRO 401: API Key inválida!")
            print("        → Verifique se OWM_API_KEY está correto")
            print("        → A chave pode demorar até 2h para ativar após criar conta")
            return None

        if resposta.status_code == 404:
            print(f"[Clima] ❌ ERRO 404: Cidade '{cidade}' não encontrada!")
            print(f"        → Tente variações: 'Sao Paulo', 'Rio de Janeiro'")
            return None

        if resposta.status_code == 429:
            print("[Clima] ❌ ERRO 429: Limite de requisições atingido!")
            print("        → Plano gratuito: 60 req/min, 1.000.000 req/mês")
            return None

        if resposta.status_code != 200:
            print(f"[Clima] ❌ Erro HTTP {resposta.status_code}: {resposta.text[:200]}")
            return None

        # ── Passo 5: Processar resposta JSON ──────────────────────────────────
        raw = resposta.json()

        # Pega o código do ícone para mapear emoji
        weather_list = raw.get("weather", [{}])
        icone_codigo = weather_list[0].get("icon", "01d")[:2] if weather_list else "01"
        emoji        = ICONES_CLIMA.get(icone_codigo, "🌡️")
        descricao    = weather_list[0].get("description", "indefinido") if weather_list else "indefinido"

        # Dados principais (segurança extra com fallback)
        main_data   = raw.get("main", {})
        wind_data   = raw.get("wind", {})
        sys_data    = raw.get("sys", {})
        clouds_data = raw.get("clouds", {})

        # Monta dicionário limpo e organizado
        dados = {
            # Localização
            "cidade":           raw.get("name", cidade),
            "pais":             sys_data.get("country", pais),
            "fonte_cidade":     fonte_cidade,

            # Temperaturas (já em Celsius por causa de UNIDADE="metric")
            "temperatura":      round(main_data.get("temp", 0),       1),
            "sensacao_termica": round(main_data.get("feels_like", 0), 1),
            "temp_min":         round(main_data.get("temp_min", 0),   1),
            "temp_max":         round(main_data.get("temp_max", 0),   1),

            # Condições
            "umidade":          main_data.get("humidity", 0),       # %
            "descricao":        descricao,                          # ex: "chuva leve"
            "emoji":            emoji,

            # Vento e visibilidade
            "vento_kmh":        round(wind_data.get("speed", 0) * 3.6, 1),  # converte m/s para km/h
            "vento_direcao":    wind_data.get("deg", 0),             # graus (0=Norte, 90=Leste)
            "visibilidade_km":  round(raw.get("visibility", 10000) / 1000, 1),

            # Céu
            "nuvens_pct":       clouds_data.get("all", 0),  # % de cobertura de nuvens

            # Chuva (se houver)
            "chuva_1h_mm":      raw.get("rain", {}).get("1h", 0),
            "neve_1h_mm":       raw.get("snow", {}).get("1h", 0),

            # Sol
            "nascer_sol":       datetime.datetime.fromtimestamp(sys_data.get("sunrise", 0)).strftime("%H:%M") if sys_data.get("sunrise") else "--:--",
            "por_sol":          datetime.datetime.fromtimestamp(sys_data.get("sunset", 0)).strftime("%H:%M") if sys_data.get("sunset") else "--:--",

            # Pressão atmosférica (hPa)
            "pressao_hpa":      main_data.get("pressure", 0),

            # Metadados
            "timestamp":        datetime.datetime.now().strftime("%d/%m/%Y às %H:%M"),
            "timestamp_unix":   time.time(),
        }

        # ── Passo 6: Salvar no cache ───────────────────────────────────────────
        _salvar_cache(dados, chave_cache)
        print(f"[Clima] ✅ Dados obtidos: {dados['temperatura']}°C, {dados['descricao']}")

        return dados

    # ── Passo 7: Tratar erros de conexão ─────────────────────────────────────
    except requests.exceptions.ConnectionError:
        print("[Clima] ❌ Sem conexão com a internet.")
        print("        → Verifique sua rede e tente novamente")
        # Tenta retornar cache mesmo que expirado como último recurso
        dados_velhos = _carregar_cache(chave_cache + "_expired")
        if dados_velhos:
            print("[Clima] ⚠️  Retornando dados em cache (podem estar desatualizados)")
            return dados_velhos
        return None

    except requests.exceptions.Timeout:
        print(f"[Clima] ❌ Timeout ({TIMEOUT}s). Servidor lento ou sem internet.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"[Clima] ❌ Erro na requisição HTTP: {e}")
        return None

    except KeyError as e:
        print(f"[Clima] ❌ Estrutura inesperada na resposta da API: campo {e} não encontrado")
        print(f"        → Resposta recebida: {raw}")
        return None

    except json.JSONDecodeError:
        print("[Clima] ❌ A API retornou resposta inválida (não é JSON)")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 📅  BUSCA DE PREVISÃO (PRÓXIMOS DIAS)
# ══════════════════════════════════════════════════════════════════════════════

def buscar_previsao(cidade: str = None, pais: str = None, dias: int = 3) -> list | None:
    """
    Busca a previsão do tempo para os próximos dias.
    A OpenWeatherMap fornece previsão de até 5 dias, a cada 3 horas.

    Parâmetros:
        cidade → Nome da cidade. Se None, usa CIDADE_PADRAO.
        pais   → Código do país.
        dias   → Quantos dias de previsão (1 a 5). Padrão: 3.

    Retorna:
        Lista de dicionários, um por dia:
        [
            {
                "data":       "06/05",
                "dia_semana": "terça-feira",
                "temp_max":   25.0,
                "temp_min":   15.0,
                "descricao":  "chuva leve",
                "emoji":      "🌧️",
                "umidade":    75,
            },
            ...
        ]
        Ou None se falhar.
    """

    # Usa cidade padrão se não informada
    if not cidade:
        local = detectar_cidade_por_ip()
        if local:
            cidade = local["cidade"]
            pais   = local["pais"]
        else:
            cidade = CIDADE_PADRAO
            pais   = PAIS_PADRAO

    # Verifica cache de previsão
    chave_cache = f"previsao_{cidade}_{pais}".lower().replace(" ", "_")
    dados_cache = _carregar_cache(chave_cache)
    if dados_cache:
        return dados_cache

    local_query = f"{cidade},{pais}" if pais else cidade

    # A API retorna previsão a cada 3h. Para N dias precisamos de N*8 registros.
    # Máximo da API: 40 registros (5 dias)
    cnt = min(dias * 8, 40)

    parametros = {
        "q":     local_query,
        "appid": OWM_API_KEY,
        "units": UNIDADE,
        "lang":  IDIOMA,
        "cnt":   cnt,
    }

    try:
        resposta = requests.get(URL_PREVISAO, params=parametros, timeout=TIMEOUT)

        if resposta.status_code == 401:
            print("[Clima] ❌ API Key inválida para previsão.")
            return None

        if resposta.status_code == 404:
            print(f"[Clima] ❌ Cidade '{cidade}' não encontrada para previsão.")
            return None

        resposta.raise_for_status()
        raw = resposta.json()

        # Agrupa os dados por dia (a API dá previsão a cada 3h)
        dias_map = {}

        for item in raw.get("list", []):
            # Converte timestamp para data
            dt       = datetime.datetime.fromtimestamp(item.get("dt", 0))
            chave_d  = dt.strftime("%d/%m")      # ex: "06/05"
            nome_dia = dt.strftime("%A")          # ex: "Tuesday"
            
            main_data    = item.get("main", {})
            weather_list = item.get("weather", [{}])
            wind_data    = item.get("wind", {})

            if chave_d not in dias_map:
                # Primeira entrada do dia: inicializa
                dias_map[chave_d] = {
                    "data":        chave_d,
                    "dia_semana":  DIAS_SEMANA_PT.get(nome_dia, nome_dia),
                    "dia_semana_en": nome_dia,
                    "temp_max":    main_data.get("temp_max", 0),
                    "temp_min":    main_data.get("temp_min", 0),
                    "descricao":   weather_list[0].get("description", "indefinido") if weather_list else "indefinido",
                    "emoji":       ICONES_CLIMA.get(weather_list[0].get("icon", "01d")[:2], "🌡️") if weather_list else "🌡️",
                    "umidade":     main_data.get("humidity", 0),
                    "vento_kmh":   round(wind_data.get("speed", 0) * 3.6, 1),
                    "chuva_mm":    item.get("rain", {}).get("3h", 0),
                    "amostras":    1,
                }
            else:
                # Atualiza máxima e mínima acumulando o dia
                d = dias_map[chave_d]
                d["temp_max"]  = max(d["temp_max"], main_data.get("temp_max", 0))
                d["temp_min"]  = min(d["temp_min"], main_data.get("temp_min", 0))
                d["umidade"]   = (d["umidade"] * d["amostras"] + main_data.get("humidity", 0)) / (d["amostras"] + 1)
                d["chuva_mm"] += item.get("rain", {}).get("3h", 0)
                d["amostras"] += 1

        # Converte para lista e arredonda valores
        resultado = []
        for dado in list(dias_map.values())[:dias]:
            dado["temp_max"] = round(dado["temp_max"], 1)
            dado["temp_min"] = round(dado["temp_min"], 1)
            dado["umidade"]  = round(dado["umidade"])
            dado["chuva_mm"] = round(dado["chuva_mm"], 1)
            del dado["amostras"]  # Remove campo interno
            resultado.append(dado)

        # Salva no cache
        _salvar_cache(resultado, chave_cache)
        print(f"[Clima] ✅ Previsão obtida para {len(resultado)} dias")

        return resultado

    except requests.exceptions.ConnectionError:
        print("[Clima] ❌ Sem conexão para buscar previsão.")
        return None
    except requests.exceptions.Timeout:
        print("[Clima] ❌ Timeout ao buscar previsão.")
        return None
    except Exception as e:
        print(f"[Clima] ❌ Erro ao buscar previsão: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 🔤  FORMATAÇÃO: TEXTO PARA VOZ (curto e natural)
# ══════════════════════════════════════════════════════════════════════════════

def formatar_para_voz(dados: dict) -> str:
    """
    Converte os dados do clima em uma frase CURTA e DIRETA para voz.
    Foco apenas em HOJE — resposta rápida e natural.

    Exemplo de saída:
        "Em Curitiba, faz 18 graus agora com nuvens dispersas.
         Mínima de 14 e máxima de 22. Hoje não deve chover."
    """
    if not dados:
        return "Não foi possível obter os dados do clima no momento, senhor."

    # Temperatura e condição (sempre presente)
    texto = (
        f"Em {dados['cidade']}, faz {dados['temperatura']} graus agora, "
        f"{dados['descricao']}. "
        f"Mínima de {dados['temp_min']} e máxima de {dados['temp_max']}. "
    )

    # Aviso de chuva — curto e direto
    chuva_atual = dados.get("chuva_1h_mm", 0)
    descricao_lower = dados.get("descricao", "").lower()
    tem_chuva = chuva_atual > 0 or any(p in descricao_lower for p in ["chuva", "chuvisco", "tempestade", "garoa"])

    if tem_chuva:
        texto += "Há chance de chuva hoje."
    else:
        texto += "Hoje não deve chover."

    return texto.strip()


def formatar_previsao_para_voz(previsoes: list) -> str:
    """
    Converte a previsão de N dias em texto natural para voz.

    Exemplo de saída:
        "Previsão do tempo: amanhã, terça-feira, mínima de 14 e máxima de 22 graus,
         com chuva leve. Depois de amanhã, quarta-feira, mínima de 16 e máxima de 24 graus,
         céu limpo."
    """
    if not previsoes:
        return "Não foi possível obter a previsão do tempo, senhor."

    partes = ["Previsão do tempo para os próximos dias:"]
    hoje   = datetime.datetime.now().date()

    for i, p in enumerate(previsoes):
        # Define o prefixo de tempo
        if i == 0:
            prefixo = "Hoje"
        elif i == 1:
            prefixo = "Amanhã"
        elif i == 2:
            prefixo = "Depois de amanhã"
        else:
            prefixo = p["dia_semana"].capitalize()

        # Aviso de chuva na previsão
        aviso_chuva = ""
        if p.get("chuva_mm", 0) > 5:
            aviso_chuva = f", com acumulado de chuva de {p['chuva_mm']} milímetros"

        partes.append(
            f"{prefixo}, {p['dia_semana']}: "
            f"mínima de {p['temp_min']} e máxima de {p['temp_max']} graus, "
            f"{p['descricao']}{aviso_chuva}."
        )

    return " ".join(partes)


# ══════════════════════════════════════════════════════════════════════════════
# 📋  FORMATAÇÃO: LOG VISUAL (detalhado para a interface)
# ══════════════════════════════════════════════════════════════════════════════

def formatar_log_clima(dados: dict) -> str:
    """
    Formata os dados do clima para exibição no log da interface da JARVIS.
    Versão detalhada com emojis e separadores visuais.
    """
    if not dados:
        return "❌ Dados de clima indisponíveis."

    # Indica fonte dos dados
    fonte_txt = {
        "ip":      "detectada por IP",
        "manual":  "informada manualmente",
        "padrao":  "padrão do sistema",
    }.get(dados.get("fonte_cidade", ""), "")

    linhas = [
        f"\n{dados['emoji']}  CLIMA ATUAL — {dados['cidade']}, {dados['pais']} ({fonte_txt})",
        "─" * 44,
        f"🌡️  Temperatura:       {dados['temperatura']}°C",
        f"🤔  Sensação térmica:  {dados['sensacao_termica']}°C",
        f"⬇️  Mínima do dia:     {dados['temp_min']}°C",
        f"⬆️  Máxima do dia:     {dados['temp_max']}°C",
        f"💧  Umidade:           {dados['umidade']}%",
        f"💨  Vento:             {dados['vento_kmh']} km/h",
        f"👁️  Visibilidade:      {dados['visibilidade_km']} km",
        f"☁️  Cobertura nuvens:  {dados['nuvens_pct']}%",
        f"📊  Pressão:           {dados['pressao_hpa']} hPa",
        f"🌅  Nascer do sol:     {dados['nascer_sol']}",
        f"🌇  Pôr do sol:        {dados['por_sol']}",
        f"📝  Condição:          {dados['descricao'].capitalize()}",
        f"🕐  Atualizado:        {dados['timestamp']}",
    ]

    # Adiciona linha de chuva apenas se houver
    if dados.get("chuva_1h_mm", 0) > 0:
        linhas.insert(-2, f"🌧️  Chuva (1h):         {dados['chuva_1h_mm']} mm")

    linhas.append("─" * 44)
    return "\n".join(linhas)


def formatar_log_previsao(previsoes: list) -> str:
    """
    Formata a previsão para exibição no log da interface.
    """
    if not previsoes:
        return "❌ Previsão indisponível."

    linhas = ["\n📅  PREVISÃO DOS PRÓXIMOS DIAS", "─" * 44]

    for p in previsoes:
        chuva_info = f" | 🌧️ {p['chuva_mm']}mm" if p.get("chuva_mm", 0) > 0.5 else ""
        linhas.append(
            f"{p['emoji']}  {p['data']} {p['dia_semana'][:3].upper()}  "
            f"↓{p['temp_min']}°C  ↑{p['temp_max']}°C  "
            f"💧{p['umidade']}%{chuva_info}  —  {p['descricao']}"
        )

    linhas.append("─" * 44)
    return "\n".join(linhas)


# ══════════════════════════════════════════════════════════════════════════════
# 🧠  DETECTOR DE INTENÇÃO DO COMANDO DE CLIMA
# ══════════════════════════════════════════════════════════════════════════════

def _extrair_cidade_do_comando(query: str) -> str | None:
    """
    Tenta extrair o nome de uma cidade do comando do usuário.

    Exemplos que funcionam:
        "clima em São Paulo"           → "São Paulo"
        "temperatura no Rio de Janeiro" → "Rio de Janeiro"
        "como está o tempo em Brasília" → "Brasília"
        "previsão para Porto Alegre"    → "Porto Alegre"

    Retorna o nome da cidade ou None se não encontrar.
    """
    q = query.lower()

    # Preposições que podem preceder um nome de cidade
    gatilhos = [
        " em ", " no ", " na ", " de ", " para ",
        " do ", " da ", " nos ", " nas ",
    ]

    for gatilho in gatilhos:
        if gatilho in q:
            # Pega tudo depois do gatilho
            pos = q.find(gatilho)
            candidato = query[pos + len(gatilho):].strip()

            # Remove palavras que claramente não são cidades
            palavras_nao_cidade = {
                "hoje", "amanhã", "agora", "momento", "já",
                "semana", "mês", "ano", "manhã", "tarde", "noite",
                "dias", "horas", "minutos",
            }

            # Pega apenas as primeiras palavras (cidades raramente têm mais de 3)
            palavras = candidato.split()
            nome_cidade_palavras = []

            for palavra in palavras[:4]:  # máximo 4 palavras
                if palavra.lower() in palavras_nao_cidade:
                    break
                # Remove pontuação e capitaliza
                p_limpa = palavra.strip("?,!.;:")
                if p_limpa:
                    nome_cidade_palavras.append(p_limpa.capitalize())

            if nome_cidade_palavras:
                return " ".join(nome_cidade_palavras)

    return None


def _detectar_se_quer_previsao(query: str) -> bool:
    """
    Detecta se o usuário quer previsão FUTURA (e não apenas o clima atual/hoje).

    Exemplos que retornam True:
        "previsão do tempo"
        "como vai estar o tempo amanhã"
        "previsão para os próximos dias"

    Exemplos que retornam False (só hoje):
        "vai chover hoje?"
        "como está o clima?"
        "tá frio?"
    """
    q = query.lower()
    # Palavras que indicam FUTURA (não hoje)
    palavras_previsao = [
        "previsão", "previsao", "próximos dias", "proximos dias",
        "amanhã", "depois de amanhã", "semana", "forecast",
    ]
    return any(p in q for p in palavras_previsao)


# ══════════════════════════════════════════════════════════════════════════════
# 🎯  FUNÇÃO PRINCIPAL — CHAMADA PELA JARVIS
# ══════════════════════════════════════════════════════════════════════════════

def cmd_clima(query: str, ui=None, speak=None) -> None:
    """
    Função principal do módulo de clima.
    Deve ser chamada dentro da função cmd() do jarvis_v8.py.

    Parâmetros:
        query → Texto do comando reconhecido (ex: "como está o clima hoje?")
        ui    → Referência para a interface JarvisUI (para add_log/add_message e speak opcional)
        speak → Callback opcional para função de fala da Jarvis

    Uso no jarvis_v8.py:
        from jarvis_clima import cmd_clima, PALAVRAS_CLIMA

        # Dentro de cmd():
        if any(p in q for p in PALAVRAS_CLIMA):
            cmd_clima(q, ui, speak)
            return
    """

    def _log(texto: str, tag: str = "info"):
        """Helper interno para logar com ou sem interface."""
        if ui:
            if hasattr(ui, "add_message"):
                ui.add_message(texto, tag)
            elif hasattr(ui, "add_log"):
                ui.add_log(texto, tag)
        else:
            print(texto)

    def _falar(texto: str):
        """Helper interno para falar com ou sem interface."""
        if speak and callable(speak):
            speak(texto)
        elif ui:
            # Usa a função speak() já existente na JARVIS se encontrada
            try:
                from __main__ import speak as main_speak
                main_speak(texto, ui)
            except ImportError:
                print(f"\n[VOZ] {texto}\n")
        else:
            print(f"\n[VOZ] {texto}\n")

    # ── Inicia processamento ──────────────────────────────────────────────────
    _log("🌤️ Consultando dados meteorológicos…", "info")

    if ui:
        try:
            ui.sig_state.emit("processing")
        except Exception:
            pass

    # ── Detecta intenção do comando ───────────────────────────────────────────
    cidade_pedida  = _extrair_cidade_do_comando(query)
    quer_previsao  = _detectar_se_quer_previsao(query)
    forcar_refresh = "atualiza" in query.lower() or "refresh" in query.lower()

    if cidade_pedida:
        _log(f"📍 Cidade identificada no comando: {cidade_pedida}", "info")

    # ── Busca clima atual ─────────────────────────────────────────────────────
    dados = buscar_clima_atual(
        cidade         = cidade_pedida,
        forcar_refresh = forcar_refresh,
    )

    if not dados:
        msg_erro = (
            "Desculpe, senhor, não consegui obter os dados do clima. "
            "Verifique a conexão com a internet."
        )
        _log("❌ Falha ao obter dados do clima. Verifique: API key, internet, nome da cidade.", "erro")
        _falar(msg_erro)
        return

    # ── Exibe no log da interface ─────────────────────────────────────────────
    _log(formatar_log_clima(dados), "info")

    # ── Prepara texto para falar ──────────────────────────────────────────────
    texto_voz = formatar_para_voz(dados)

    # ── Adiciona previsão se solicitada ───────────────────────────────────────
    if quer_previsao:
        _log("📅 Buscando previsão para os próximos dias…", "info")

        previsoes = buscar_previsao(
            cidade = cidade_pedida or dados["cidade"],
            pais   = dados["pais"],
            dias   = 3,
        )

        if previsoes:
            _log(formatar_log_previsao(previsoes), "info")
            texto_voz += " " + formatar_previsao_para_voz(previsoes)

    # ── Fala o resultado ──────────────────────────────────────────────────────
    _falar(texto_voz)


# ══════════════════════════════════════════════════════════════════════════════
# ✅  VERIFICAÇÃO DA API KEY
# ══════════════════════════════════════════════════════════════════════════════

def verificar_api_key() -> bool:
    """
    Testa se a API key está correta fazendo uma chamada de teste.
    Útil para diagnóstico quando o módulo não funcionar.

    Retorna True se a key for válida, False caso contrário.
    """
    print("\n" + "═" * 50)
    print("  VERIFICANDO API KEY DA OPENWEATHERMAP")
    print("═" * 50)

    if OWM_API_KEY == "SUA_API_KEY_AQUI":
        print("\n❌ ERRO: Você ainda não configurou a API Key!")
        print("   → Edite o arquivo jarvis_clima.py")
        print("   → Substitua 'SUA_API_KEY_AQUI' pela sua chave")
        print("   → Crie uma chave gratuita em: openweathermap.org/api")
        return False

    if len(OWM_API_KEY) != 32:
        print(f"\n⚠️  ATENÇÃO: A key tem {len(OWM_API_KEY)} caracteres.")
        print("   → Keys da OpenWeatherMap têm exatamente 32 caracteres")
        print("   → Verifique se copiou corretamente")

    print(f"\n🔑 Key configurada: {OWM_API_KEY[:8]}{'*' * 20}{OWM_API_KEY[-4:]}")
    print("🌐 Testando conexão com a API...")

    try:
        resposta = requests.get(
            URL_CLIMA_ATUAL,
            params={
                "q":     "London,GB",
                "appid": OWM_API_KEY,
                "units": "metric",
            },
            timeout=TIMEOUT
        )

        if resposta.status_code == 200:
            print("✅ API Key VÁLIDA! Conexão estabelecida com sucesso.")
            return True
        elif resposta.status_code == 401:
            print("❌ API Key INVÁLIDA!")
            print("   → Causas comuns:")
            print("   → 1. Copiou errado — verifique caractere a caractere")
            print("   → 2. Chave recém-criada — aguarde até 2 horas para ativar")
            print("   → 3. Conta bloqueada — verifique sua conta em openweathermap.org")
            return False
        else:
            print(f"⚠️  Resposta inesperada: HTTP {resposta.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Sem conexão com a internet.")
        print("   → Verifique sua rede e tente novamente")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# 🧪  TESTES — Execute este arquivo diretamente para testar tudo
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("   J.A.R.V.I.S — TESTE DO MÓDULO DE CLIMA v2.0")
    print("═" * 60)

    # ── TESTE 1: Verificação da API Key ───────────────────────────────────────
    print("\n📌 TESTE 1: Verificando API Key...")
    api_ok = verificar_api_key()
    if not api_ok:
        print("\n⚠️ Aviso: A verificação da API Key falhou (API inválida ou sem internet).")
        print("   Continuando os testes para validar o comportamento de fallback (sem internet)...")

    # ── TESTE 2: Detecção de cidade por IP ────────────────────────────────────
    print("\n\n📌 TESTE 2: Detectando cidade por IP...")
    local = detectar_cidade_por_ip()
    if local:
        print(f"   ✅ Cidade: {local['cidade']}, {local['pais']}")
        print(f"   📍 Região: {local.get('regiao', 'N/A')}")
        print(f"   🗺️  Coordenadas: {local['lat']}, {local['lon']}")
    else:
        print("   ❌ Detecção por IP falhou — será usado padrão")

    # ── TESTE 3: Clima atual da cidade detectada ──────────────────────────────
    print("\n\n📌 TESTE 3: Buscando clima atual...")
    dados = buscar_clima_atual()
    if dados:
        print(formatar_log_clima(dados))
        print(f"\n🎙️  [TEXTO PARA VOZ]:")
        print(f"   {formatar_para_voz(dados)}")
    else:
        print("   ❌ Falha ao buscar clima atual")

    # ── TESTE 4: Clima de cidade específica ───────────────────────────────────
    print("\n\n📌 TESTE 4: Testando cidade específica (São Paulo)...")
    dados_sp = buscar_clima_atual(cidade="São Paulo", pais="BR", forcar_refresh=True)
    if dados_sp:
        print(f"   ✅ {dados_sp['cidade']}: {dados_sp['temperatura']}°C — {dados_sp['descricao']}")
    else:
        print("   ❌ Falha ao buscar São Paulo")

    # ── TESTE 5: Previsão dos próximos 3 dias ─────────────────────────────────
    print("\n\n📌 TESTE 5: Buscando previsão (3 dias)...")
    previsoes = buscar_previsao(dias=3)
    if previsoes:
        print(formatar_log_previsao(previsoes))
        print(f"\n🎙️  [TEXTO PARA VOZ]:")
        print(f"   {formatar_previsao_para_voz(previsoes)}")
    else:
        print("   ❌ Falha ao buscar previsão")

    # ── TESTE 6: Extração de cidade do comando ────────────────────────────────
    print("\n\n📌 TESTE 6: Testando extração de cidades dos comandos...")
    comandos_teste = [
        "como está o clima em São Paulo?",
        "temperatura no Rio de Janeiro agora",
        "previsão para Brasília",
        "vai chover em Porto Alegre semana que vem?",
        "como está o tempo?",  # sem cidade → deve retornar None
    ]
    for cmd_teste in comandos_teste:
        cidade_extraida = _extrair_cidade_do_comando(cmd_teste)
        quer_prev = _detectar_se_quer_previsao(cmd_teste)
        print(f"   '{cmd_teste}'")
        print(f"   → Cidade: {cidade_extraida or '(detectar por IP)'} | Previsão: {quer_prev}\n")

    print("═" * 60)
    print("   ✅ TODOS OS TESTES CONCLUÍDOS")
    print("═" * 60)
    print("\nPróximos passos:")
    print("1. Copie este arquivo para a pasta do seu jarvis_v8.py")
    print("2. Adicione no topo do jarvis_v8.py:")
    print("   from jarvis_clima import cmd_clima, PALAVRAS_CLIMA")
    print("3. Dentro de cmd(), adicione antes dos outros comandos:")
    print("   if any(p in q for p in PALAVRAS_CLIMA):")
    print("       cmd_clima(q, ui)")
    print("       return")
    print("\nBoa sorte, sir! 🤖\n")
