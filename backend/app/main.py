from configparser import ConfigParser
from pathlib import Path

import psycopg


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BASE_DIR / "database" / "database.ini"


def load_db_config(filename=DEFAULT_CONFIG_PATH, section="postgresql"):
    parser = ConfigParser()
    read_files = parser.read(filename)

    if not read_files:
        raise FileNotFoundError(f"Could not read config file: {filename}")

    if not parser.has_section(section):
        raise KeyError(f"Section '{section}' not found in {filename}")

    config = {key: value for key, value in parser.items(section) if value}

    if "database" in config and "dbname" not in config:
        config["dbname"] = config.pop("database")

    return config


def get_connection():
    db_config = load_db_config()
    return psycopg.connect(**db_config)


def test_connection():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()

    print("Connection successful.")
    if version:
        print(f"PostgreSQL version: {version[0]}")


def list_tables():
    query = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    if not rows:
        print("No user tables found.")
        return

    print("Tables:")
    for schema, table in rows:
        print(f"- {schema}.{table}")


def run_select_query(sql):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc.name for desc in cur.description] if cur.description else []

    if columns:
        print(" | ".join(columns))
        print("-" * (len(" | ".join(columns))))

    for row in rows:
        print(" | ".join(str(value) for value in row))

    if not rows:
        print("Query returned no rows.")


def run_write_query(sql):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print("Statement executed successfully.")


def prompt_custom_sql():
    sql = input("Enter SQL: ").strip()
    if not sql:
        print("No SQL entered.")
        return

    if sql.lower().startswith("select"):
        run_select_query(sql)
    else:
        run_write_query(sql)


def main():
    actions = {
        "1": ("Test database connection", test_connection),
        "2": ("List tables", list_tables),
        "3": ("Run SELECT query", lambda: run_select_query(input("Enter SELECT query: ").strip())),
        "4": ("Run custom SQL", prompt_custom_sql),
    }

    print("Simple Neon/PostgreSQL helper")
    print(f"Using config file: {DEFAULT_CONFIG_PATH}")

    while True:
        print("\nChoose an option:")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        print("5. Exit")

        choice = input("Selection: ").strip()

        if choice == "5":
            print("Goodbye.")
            break

        action = actions.get(choice)
        if not action:
            print("Invalid choice.")
            continue

        try:
            action[1]()
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()

