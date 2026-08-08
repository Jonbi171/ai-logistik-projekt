from configparser import ConfigParser
from pathlib import Path
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import sessionmaker

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

def boot():
    db_config = load_db_config()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
        port=int(db_config["port"]),
        database=db_config["dbname"],
        query={"sslmode": db_config["sslmode"]},
    )

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, SessionLocal