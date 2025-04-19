
import sqlite3
import logging
import os
from pathlib import Path

# Constants
DB_BASE_PATH = "data/databases"

def init_database_directory():
    """Initialize the database directory at startup."""
    Path(DB_BASE_PATH).mkdir(parents=True, exist_ok=True)

def ensure_db_directory(db_path):
    """Ensure the directory for the database exists."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)

def get_connection(db_name):
    """Get a database connection with proper directory initialization."""
    ensure_db_directory(db_name)
    return sqlite3.connect(db_name)

def store_in_database(data, db_name, table_name, schema):
    """
    Store extracted data into a SQLite database with dynamic table creation.
    Handles AUTOINCREMENT columns automatically.
    
    Args:
        data: List of tuples containing the data to insert
        db_name: Path to the SQLite database file
        table_name: Name of the table to create/insert into
        schema: SQL schema string for table creation
    
    Returns:
        bool: True if operation was successful, False otherwise
    """
    try:
        conn = get_connection(db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
        except sqlite3.OperationalError as e:
            logging.error(f"Error creating table {table_name}: {e}")
            conn.close()
            return False

        if data:
            # Filter out AUTOINCREMENT columns for INSERT
            columns = ", ".join(
                col.split()[0] for col in schema.split(",")
                if "AUTOINCREMENT" not in col.upper()
            )
            placeholders = ", ".join("?" for _ in data[0])
            
            try:
                cursor.executemany(
                    f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                    data
                )
                conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Error inserting data into {table_name}: {e}")
                conn.rollback()
                conn.close()
                return False
                
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return False

# Initialize database directory when module is imported
init_database_directory()
