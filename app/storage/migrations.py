from app.database import Database


def run_migrations(database: Database) -> None:
    database.initialize()
