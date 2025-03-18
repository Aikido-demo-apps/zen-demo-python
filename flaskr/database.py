import os
import re
from urllib.parse import urlparse
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from flask import current_app

class Pet:
    def __init__(self, id, name, owner):
        self.id = id
        self.name = name
        self.owner = owner

class DatabaseHelper:
    # Regex pattern for input validation
    REGEX = r'^[A-Za-z0-9 ,-.]+$'

    @staticmethod
    def create_db_pool():
        """Create and return database connection pool"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")

        # Parse the database URL
        url = urlparse(database_url)

        # Create connection pool
        pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            sslmode='disable'
        )
        return pool

    @staticmethod
    @contextmanager
    def get_db_connection():
        """Context manager for database connections"""
        conn = current_app.config['db_pool'].getconn()
        try:
            yield conn
        finally:
            current_app.config['db_pool'].putconn(conn)

    @staticmethod
    def is_valid_input(input_str):
        """Validate input string against regex pattern"""
        return bool(re.match(DatabaseHelper.REGEX, input_str))

    @staticmethod
    def clear_all():
        """Clear all pets from the database"""
        try:
            with DatabaseHelper.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM pets")
                    rows_affected = cur.rowcount
                    conn.commit()
                    print(f"{rows_affected} pets have been removed from the database.")
        except Exception as e:
            print(f"Database error occurred: {e}")
            conn.rollback()

    @staticmethod
    def get_all_pets():
        """Get all pets from the database"""
        pets = []
        try:
            with DatabaseHelper.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM pets")
                    for row in cur.fetchall():
                        id, name, owner = row

                        # Validate input for XSS risks
                        if not DatabaseHelper.is_valid_input(name):
                            name = "[REDACTED: XSS RISK]"
                        if not DatabaseHelper.is_valid_input(owner):
                            owner = "[REDACTED: XSS RISK]"

                        pets.append(Pet(id, name, owner))
        except Exception as e:
            print(f"Database error occurred: {e}")
        return pets

    @staticmethod
    def get_pet_by_id(id):
        """Get a pet by its ID"""
        try:
            with DatabaseHelper.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM pets WHERE pet_id = %s", (id,))
                    row = cur.fetchone()
                    if row:
                        return Pet(row[0], row[1], row[2])
        except Exception as e:
            print(f"Database error occurred: {e}")
        return Pet(0, "Unknown", "Unknown")

    @staticmethod
    def create_pet_by_name(pet_name):
        """Create a new pet"""
        try:
            with DatabaseHelper.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Using parameterized query to prevent SQL injection
                    cur.execute(
                        "INSERT INTO pets (pet_name, owner) VALUES (%s, %s)",
                        (pet_name, 'Aikido Security')
                    )
                    conn.commit()
                    return cur.rowcount
        except Exception as e:
            print(f"Database error occurred: {e}")
            conn.rollback()
        return -1

# Flask application setup
def init_database(app):
    """Initialize the Flask application with database pool"""
    app.config['db_pool'] = DatabaseHelper.create_db_pool()

    @app.teardown_appcontext
    def close_db_pool(exception):
        """Close the database pool when the application context ends"""
        db_pool = app.config.get('db_pool')
        if db_pool:
            db_pool.closeall()
