import sqlite3
import psycopg2
from urllib.parse import urlparse
import datetime
import os

def sanitize_row(row):
    return tuple(
        value.isoformat() if isinstance(value, (datetime.datetime, datetime.date)) else value
        for value in row
    )

def convert_postgres_to_sqlite(pg_conn_str, sqlite_file):
    result = urlparse(pg_conn_str)
    pg_conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    pg_cursor = pg_conn.cursor()
    sqlite_conn = sqlite3.connect(sqlite_file)
    sqlite_cursor = sqlite_conn.cursor()

    # Get all table names
    pg_cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = pg_cursor.fetchall()

    for table_name_tuple in tables:
        table_name = table_name_tuple[0]

        # Get columns and types
        pg_cursor.execute(f"""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = '{table_name}';
        """)
        columns = pg_cursor.fetchall()
        column_names = [col[0] for col in columns]

        # Map PostgreSQL types to SQLite types
        column_defs = []
        for col_name, col_type in columns:
            if col_type in ['integer', 'bigint', 'smallint']:
                sqlite_type = 'INTEGER'
            elif col_type in ['real', 'double precision', 'numeric', 'decimal']:
                sqlite_type = 'REAL'
            elif col_type == 'boolean':
                sqlite_type = 'BOOLEAN'
            else:
                sqlite_type = 'TEXT'
            # Add AUTOINCREMENT for id column
            if col_name == 'id':
                column_defs.append(f"{col_name} INTEGER PRIMARY KEY AUTOINCREMENT")
            else:
                column_defs.append(f"{col_name} {sqlite_type}")
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)});"
        sqlite_cursor.execute(create_table_sql)

        # Copy data
        quoted_columns = [f'"{col}"' for col in column_names]
        select_sql = f'SELECT {", ".join(quoted_columns)} FROM "{table_name}";'
        pg_cursor.execute(select_sql)
        rows = pg_cursor.fetchall()
        formatted_rows = [sanitize_row(row) for row in rows if isinstance(row, (list, tuple)) and len(row) == len(column_names)]
        placeholders = ', '.join(['?'] * len(column_names))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders});"
        if formatted_rows:
            sqlite_cursor.executemany(insert_sql, formatted_rows)

    sqlite_conn.commit()
    sqlite_conn.close()
    pg_cursor.close()
    pg_conn.close()
    print(f"Data has been successfully exported to {sqlite_file}")

# Usage
from dotenv import load_dotenv
load_dotenv()
POSTGRES_CONN_STR = os.getenv("REMOTE_DATABASE_URL")
PARENT_DIR = os.path.dirname(os.path.dirname(__file__))
SQLITE_DB_FILE = os.path.join(PARENT_DIR, "app.db")
convert_postgres_to_sqlite(POSTGRES_CONN_STR, SQLITE_DB_FILE)
