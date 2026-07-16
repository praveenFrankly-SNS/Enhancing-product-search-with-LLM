# =====================================================================
# Product Search — Ingestion: JDBC Reader Helper
# =====================================================================
# Handles PostgreSQL database connection credentials, JDBC URLs,
# parallel table loading, and database connectivity checks via Spark JDBC.
# =====================================================================

import os
from typing import Tuple
from pyspark.sql import SparkSession, DataFrame


def resolve_db_credentials(secret_scope: str, dbutils = None) -> Tuple[str, str, str, str, str]:
    """
    Retrieves database connection credentials from Databricks Secrets.
    Returns: (host, port, database_name, username, password)
    """
    if dbutils is not None:
        try:
            # Attempt to retrieve with 'db-' prefix first
            try:
                db_host = dbutils.secrets.get(scope=secret_scope, key="db-host")
                db_port = dbutils.secrets.get(scope=secret_scope, key="db-port")
                db_name = dbutils.secrets.get(scope=secret_scope, key="db-name")
                db_user = dbutils.secrets.get(scope=secret_scope, key="db-user")
                db_pass = dbutils.secrets.get(scope=secret_scope, key="db-password")
            except Exception:
                # Fallback to standard secret keys
                db_host = dbutils.secrets.get(scope=secret_scope, key="host")
                db_port = dbutils.secrets.get(scope=secret_scope, key="port")
                db_name = dbutils.secrets.get(scope=secret_scope, key="database")
                db_user = dbutils.secrets.get(scope=secret_scope, key="username")
                db_pass = dbutils.secrets.get(scope=secret_scope, key="password")
            return db_host, db_port, db_name, db_user, db_pass
        except Exception as e:
            raise RuntimeError(
                f"Failed to retrieve database credentials from Databricks Secret Scope '{secret_scope}'. "
                f"Ensure the scope exists and has keys like ('db-host', 'db-port', 'db-name', 'db-user', 'db-password') "
                f"or ('host', 'port', 'database', 'username', 'password'). Error: {str(e)}"
            ) from e

    # Local fallback for CLI / Unit Test context where dbutils is not available
    db_host = os.getenv("DB_HOST", "aws-1-ap-south-1.pooler.supabase.com")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")
    db_user = os.getenv("DB_USER", "postgres.wkrauxubcjzrcskvsyag")
    db_pass = os.getenv("DB_PASSWORD", "25b$puEr/*vu&$n")
    
    return db_host, db_port, db_name, db_user, db_pass


def read_jdbc_table(spark: SparkSession, secret_scope: str, source_table: str, 
                    num_partitions: int = 4, dbutils = None) -> DataFrame:
    """
    Reads a table from Supabase PostgreSQL using parallel PySpark JDBC.
    """
    db_host, db_port, db_name, db_user, db_pass = resolve_db_credentials(secret_scope, dbutils)
    
    jdbc_url = f"jdbc:postgresql://{db_host}:{db_port}/{db_name}"
    connection_properties = {
        "user": db_user,
        "password": db_pass,
        "driver": "org.postgresql.Driver",
        "numPartitions": str(num_partitions)
    }
    
    return spark.read.jdbc(
        url=jdbc_url,
        table=source_table,
        properties=connection_properties
    )


def check_jdbc_connection(spark: SparkSession, secret_scope: str, dbutils = None) -> bool:
    """
    Checks database connectivity by reading a dummy query via Spark JDBC.
    Returns True if connection succeeded, otherwise raises an exception.
    """
    db_host, db_port, db_name, db_user, db_pass = resolve_db_credentials(secret_scope, dbutils)
    
    jdbc_url = f"jdbc:postgresql://{db_host}:{db_port}/{db_name}"
    connection_properties = {
        "user": db_user,
        "password": db_pass,
        "driver": "org.postgresql.Driver"
    }
    
    try:
        # Run a tiny SELECT statement to verify credentials and connectivity
        test_df = spark.read.jdbc(
            url=jdbc_url,
            table="(SELECT 1) as connection_test",
            properties=connection_properties
        )
        test_df.collect()
        return True
    except Exception as e:
        raise RuntimeError(
            f"JDBC connection verification failed for host {db_host}. Error: {str(e)}"
        ) from e
