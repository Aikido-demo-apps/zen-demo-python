import os
import re
from urllib.parse import urlparse
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from flask import current_app

class DatabaseHelper:
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

        # Create table
        with pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.pets
                    (
                    pet_id integer NOT NULL GENERATED ALWAYS AS IDENTITY (START 1 INCREMENT 1 ),
                    pet_name character varying(255) NOT NULL,
                    owner character varying(255) NOT NULL,
                    CONSTRAINT pet_pkey PRIMARY KEY (pet_id)
                    )
                """)
                conn.commit()

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

                        pets.append({
                            'pet_id': str(id),
                            'name': str(name),
                            'owner': str(owner),
                        })
        except Exception as e:
            print(f"Database error occurred: {e}")

        return pets

    @staticmethod
    def create_pet_by_name(pet_name):
        """Create a new pet"""
        with DatabaseHelper.get_db_connection() as conn:
            with conn.cursor() as cur:
                query = f"INSERT INTO pets (pet_name, owner) VALUES ('{pet_name}', 'Aikido Security')"
                cur.execute(query)
                conn.commit()
                return cur.rowcount

# Flask application setup
def init_database(app):
    """Initialize the Flask application with database pool"""
    app.config['db_pool'] = DatabaseHelper.create_db_pool()
