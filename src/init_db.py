"""Initialize the database schema."""

from src.storage import DatabaseManager
from src.config import get_settings


def main():
    """Initialize database schema."""
    settings = get_settings()
    print(f"Initializing database at: {settings.duckdb_path}")
    
    db = DatabaseManager()
    db.init_schema()
    db.close()
    
    print("Database initialized successfully!")


if __name__ == "__main__":
    main()
