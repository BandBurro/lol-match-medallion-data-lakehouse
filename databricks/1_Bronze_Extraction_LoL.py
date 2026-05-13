import requests
from pyspark.sql.functions import lit
from pyspark.sql import Row

# Mantemos apenas o widget do PUUID (que não é uma senha crítica)
dbutils.widgets.text("puuid", "B7hVY8JCtnnjfTG89uULeZ2h3nYxIrB5uchwhc2NPZ8AAbc3zSlEW0fp8aGpXxnN_txKpr28lXWKew")

# Buscamos a chave DIRETAMENTE do cofre que você criou via CLI
API_KEY = dbutils.secrets.get(scope="riot-api", key="developer-key")

# Pegamos o valor do PUUID do widget acima
PUUID = dbutils.widgets.get("puuid")
REGION = "americas"

# 2. Busca dos IDs das últimas 20 partidas
url_match_ids = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{PUUID}/ids?start=0&count=20&api_key={API_KEY}"
response_ids = requests.get(url_match_ids)

if response_ids.status_code == 200:
    match_ids = response_ids.json()
    print(f"Partidas encontradas: {len(match_ids)}")
else:
    raise Exception(f"Erro ao buscar IDs: {response_ids.status_code}")

# 3. Extração dos detalhes de cada partida
# CORREÇÃO: Criamos a variável 'json_strings' que o Spark estava procurando
json_strings = []

for m_id in match_ids:
    url_detail = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{m_id}?api_key={API_KEY}"
    
    # CORREÇÃO NITTY-GRITTY: Usamos '.text' em vez de '.json()'.
    # Isso captura a string JSON crua da API, sendo a forma mais segura e performática 
    # de salvar dados na Camada Bronze sem que o Spark tente adivinhar o schema.
    detail_raw_string = requests.get(url_detail).text
    json_strings.append(detail_raw_string)

# 4. Salvando na Camada Bronze (Compatível com Serverless)
# Criamos o DataFrame diretamente a partir das strings JSON
# Cada linha terá uma única coluna chamada 'json_payload'
df_bronze = spark.createDataFrame([Row(json_payload=s) for s in json_strings])

# Agora salvamos na tabela Delta da Camada Bronze
# Não haverá erro de inferência porque para o Spark isso é apenas texto (String)
df_bronze.write.format("delta").mode("overwrite").saveAsTable("bronze_matches_lol")

print(f"Sucesso! {df_bronze.count()} partidas salvas como strings na bronze_matches_lol.")

# Verificando as 5 primeiras linhas da sua nova tabela Bronze
display(spark.table("bronze_matches_lol").limit(5))