import os
import mysql.connector


def databaseConfig():
    """Create and return a MySQL connection.

    Environment variables supported:
      - DB_HOST (default: localhost)
      - DB_USER
      - DB_PASSWORD
      - DB_NAME
      - DB_PORT (default: 3306)

    If env vars are not set, fallback to localhost/defaults.
    """
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "ecommerce")
    port = int(os.getenv("DB_PORT", "3306"))

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        autocommit=False,
    )

