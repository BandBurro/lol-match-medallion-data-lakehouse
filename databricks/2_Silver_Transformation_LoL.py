# Databricks notebook source
from pyspark.sql.functions import col, udf, lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType
import json

# 1. Parâmetro: O seu PUUID (para o código ignorar os outros 9 jogadores da partida)
dbutils.widgets.text("puuid", "B7hVY8JCtnnjfTG89uULeZ2h3nYxIrB5uchwhc2NPZ8AAbc3zSlEW0fp8aGpXxnN_txKpr28lXWKew")
PUUID = dbutils.widgets.get("puuid")

# 2. Lendo os dados brutos da Camada Bronze
df_bronze = spark.read.table("bronze_matches_lol")

# 3. Definindo o "Molde" (Schema) da nossa tabela Silver
schema_silver = StructType([
    StructField("match_id", StringType(), True),
    StructField("champion", StringType(), True),
    StructField("kills", IntegerType(), True),
    StructField("deaths", IntegerType(), True),
    StructField("assists", IntegerType(), True),
    StructField("win", BooleanType(), True)
])

# 4. A Função "Nitty-Gritty": Abre o JSON, acha o seu PUUID e pega os dados
def extrair_meus_dados(json_str, meu_puuid):
    try:
        data = json.loads(json_str)
        match_id = data.get("metadata", {}).get("matchId", "")
        participants = data.get("info", {}).get("participants", [])
        
        for p in participants:
            if p.get("puuid") == meu_puuid:
                return (match_id, p.get("championName"), p.get("kills"), p.get("deaths"), p.get("assists"), p.get("win"))
        return None
    except:
        return None

# Convertendo a função Python em uma ferramenta do Spark
pescar_dados_udf = udf(extrair_meus_dados, schema_silver)

# 5. Aplicando a transformação linha por linha de forma distribuída
df_silver = df_bronze.withColumn("dados_limpos", pescar_dados_udf(col("json_payload"), lit(PUUID)))

# 6. Abrindo o molde em colunas reais e removendo eventuais erros
df_final = df_silver.select("dados_limpos.*").filter(col("match_id").isNotNull())

# 7. Salvando a tabela limpa na Camada Silver
df_final.write.format("delta").mode("overwrite").saveAsTable("silver_matches_lol")

print(f"Sucesso! {df_final.count()} partidas processadas na Camada Silver.")
display(df_final)