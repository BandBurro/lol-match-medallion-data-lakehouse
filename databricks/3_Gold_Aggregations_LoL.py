from pyspark.sql.functions import col, sum, count, round, avg

# 1. Lendo os dados limpos da Camada Silver
df_silver = spark.read.table("silver_matches_lol")

# 2. A Mágica da Camada Gold: Agrupando por Campeão e calculando estatísticas
df_gold = df_silver.groupBy("champion").agg(
    count("*").alias("total_partidas"),
    sum(col("win").cast("int")).alias("vitorias"),
    round(avg("kills"), 1).alias("media_kills"),
    round(avg("deaths"), 1).alias("media_deaths"),
    round(avg("assists"), 1).alias("media_assists")
).withColumn(
    # Calculando a taxa de vitória em porcentagem
    "win_rate_pct", round((col("vitorias") / col("total_partidas")) * 100, 1)
).orderBy(col("total_partidas").desc()) # Ordena pelos campeões mais jogados

# 3. Salvando a tabela final na Camada Gold
# 3.1. Primeiro, criamos uma View temporária com os novos dados calculados
df_gold.createOrReplaceTempView("v_new_stats")

# 3.2. Executamos o MERGE usando SQL (o padrão mais robusto do Delta Lake)
spark.sql("""
    MERGE INTO gold_champion_stats_lol AS target
    USING v_new_stats AS source
    ON target.champion = source.champion
    WHEN MATCHED THEN
      UPDATE SET 
        target.total_partidas = source.total_partidas,
        target.vitorias = source.vitorias,
        target.media_kills = source.media_kills,
        target.media_deaths = source.media_deaths,
        target.media_assists = source.media_assists,
        target.win_rate_pct = source.win_rate_pct
    WHEN NOT MATCHED THEN
      INSERT *
""")

print(f"Sucesso! Estatísticas agregadas para {df_gold.count()} campeões.")
display(df_gold)