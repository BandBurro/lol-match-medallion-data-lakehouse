from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'matheus',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='lol_etl_medallion',
    default_args=default_args,
    description='Orquestra o pipeline de LoL: Bronze -> Silver',
    schedule='@daily',
    start_date=datetime(2026, 5, 2), 
    catchup=False,
    tags=['league_of_legends', 'bronze', 'silver', 'databricks'],
) as dag:

    # Tarefa 1: Extração (Substitua pelo ID do seu Job Bronze)
    extrair_bronze = DatabricksRunNowOperator(
        task_id='extrair_partidas_lol_bronze',
        databricks_conn_id='databricks_default', 
        job_id=517916893315560, 
    )

    # Tarefa 2: Transformação (Substitua pelo ID do seu Job Silver)
    transformar_silver = DatabricksRunNowOperator(
        task_id='transformar_partidas_lol_silver',
        databricks_conn_id='databricks_default', 
        job_id=275330635706256, 
    )

    # A Ordem Mágica da Engenharia de Dados:
    # A Silver SÓ executa se a Bronze terminar com sucesso absoluto.
    extrair_bronze >> transformar_silver

    # ... (Seu código existente da Bronze e Silver) ...

    # Tarefa 3: Agregação (Substitua pelo ID do seu Job Gold)
    agregar_gold = DatabricksRunNowOperator(
        task_id='calcular_metricas_lol_gold',
        databricks_conn_id='databricks_default', 
        job_id=155591447456661, 
    )

    # A Ordem Mágica Atualizada: Bronze -> Silver -> Gold
    extrair_bronze >> transformar_silver >> agregar_gold