import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import argparse
from typing import List, Dict, Any
import logging
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseToSQLiteConverter:
    def __init__(self, supabase_url: str, sqlite_path: str = "app.db"):
        self.supabase_url = supabase_url
        self.sqlite_path = sqlite_path
        self.pg_conn = None
        self.sqlite_conn = None
        
    def parse_supabase_url(self) -> Dict[str, str]:
        """Parse Supabase connection URL into connection parameters"""
        try:
            # Handle special case where URL might be in Supabase connection string format
            if "postgresql://" not in self.supabase_url and "@" in self.supabase_url:
                # Try to reformat if it's a direct Supabase connection string
                pattern = r"postgres\.([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
                match = re.search(pattern, self.supabase_url)
                if match:
                    user, password, host, port, dbname = match.groups()
                    return {
                        'dbname': dbname,
                        'user': user,
                        'password': password,
                        'host': host,
                        'port': port
                    }
            
            parsed = urlparse(self.supabase_url)
            
            # Extract components from the URL
            dbname = parsed.path[1:] if parsed.path.startswith('/') else parsed.path
            user = parsed.username
            password = parsed.password
            host = parsed.hostname
            port = parsed.port or 5432
            
            return {
                'dbname': dbname,
                'user': user,
                'password': password,
                'host': host,
                'port': port
            }
        except Exception as e:
            logger.error(f"Failed to parse Supabase URL: {e}")
            logger.error(f"URL format: {self.supabase_url}")
            raise
    
    def connect_to_postgres(self) -> None:
        """Connect to Supabase PostgreSQL database"""
        try:
            connection_params = self.parse_supabase_url()
            logger.info(f"Connecting to PostgreSQL with params: { {k: v for k, v in connection_params.items() if k != 'password'} }")
            self.pg_conn = psycopg2.connect(**connection_params, cursor_factory=RealDictCursor)
            logger.info("Connected to Supabase PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def connect_to_sqlite(self) -> None:
        """Connect to SQLite database"""
        try:
            # Remove existing database file if it exists
            if os.path.exists(self.sqlite_path):
                os.remove(self.sqlite_path)
                logger.info(f"Removed existing SQLite database: {self.sqlite_path}")
                
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            # Enable foreign keys
            self.sqlite_conn.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create SQLite tables based on your Flask-SQLAlchemy models"""
        try:
            with self.sqlite_conn:
                # Create follows table
                self.sqlite_conn.execute("""
                    CREATE TABLE IF NOT EXISTS follows (
                        follower_id INTEGER NOT NULL,
                        followed_id INTEGER NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (follower_id, followed_id),
                        FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (followed_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Create users table
                self.sqlite_conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        email VARCHAR(64) UNIQUE,
                        username VARCHAR(64) UNIQUE,
                        password_hash VARCHAR(256),
                        confirmed BOOLEAN DEFAULT FALSE,
                        name VARCHAR(64),
                        headline VARCHAR(128),
                        education VARCHAR(128),
                        talks_about VARCHAR(128),
                        location VARCHAR(64),
                        about_me TEXT,
                        avatar_hash VARCHAR(32),
                        member_since DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create posts table
                self.sqlite_conn.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY,
                        body TEXT,
                        body_html TEXT,
                        post_name VARCHAR(100),
                        media_url VARCHAR(255),
                        media_type VARCHAR(20),
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        featured BOOLEAN DEFAULT FALSE,
                        author_id INTEGER,
                        FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Create comments table
                self.sqlite_conn.execute("""
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY,
                        body TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        author_id INTEGER NOT NULL,
                        post_id INTEGER NOT NULL,
                        FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
                    )
                """)
                
                # Create likes table
                self.sqlite_conn.execute("""
                    CREATE TABLE IF NOT EXISTS likes (
                        id INTEGER PRIMARY KEY,
                        author_id INTEGER NOT NULL,
                        post_id INTEGER NOT NULL,
                        FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
                    )
                """)
                
            logger.info("Created all tables successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def copy_table_data(self, table_name: str, columns: List[str] = None) -> None:
        """Copy data from PostgreSQL table to SQLite table"""
        try:
            with self.pg_conn.cursor() as pg_cursor:
                # Get column names if not provided
                if columns is None:
                    pg_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
                    columns = [desc[0] for desc in pg_cursor.description]
                
                # Get all data from PostgreSQL
                pg_cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
                rows = pg_cursor.fetchall()
                
                if not rows:
                    logger.info(f"No data found in table: {table_name}")
                    return
                
                # Prepare SQL for insertion
                placeholders = ', '.join(['?' for _ in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                # Insert data into SQLite
                with self.sqlite_conn:
                    sqlite_cursor = self.sqlite_conn.cursor()
                    for row in rows:
                        values = []
                        for col in columns:
                            value = row[col]
                            # Handle datetime objects
                            if isinstance(value, datetime):
                                value = value.strftime('%Y-%m-%d %H:%M:%S.%f')
                            # Handle boolean values
                            elif isinstance(value, bool):
                                value = 1 if value else 0
                            values.append(value)
                        sqlite_cursor.execute(insert_sql, values)
                
                logger.info(f"Copied {len(rows)} rows to table: {table_name}")
                
        except Exception as e:
            logger.error(f"Failed to copy data for table {table_name}: {e}")
            raise
    
    def copy_data_with_relationships(self) -> None:
        """Copy data in the correct order to maintain foreign key relationships"""
        try:
            # Copy users first (they are referenced by other tables)
            logger.info("Copying users data...")
            self.copy_table_data('users')
            
            # Copy posts (references users)
            logger.info("Copying posts data...")
            self.copy_table_data('posts')
            
            # Copy follows (references users)
            logger.info("Copying follows data...")
            self.copy_table_data('follows')
            
            # Copy comments (references users and posts)
            logger.info("Copying comments data...")
            self.copy_table_data('comments')
            
            # Copy likes (references users and posts)
            logger.info("Copying likes data...")
            self.copy_table_data('likes')
            
        except Exception as e:
            logger.error(f"Failed to copy data with relationships: {e}")
            raise
    
    def verify_data_integrity(self) -> None:
        """Verify that data was copied correctly and relationships are intact"""
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Check row counts
            tables = ['users', 'posts', 'follows', 'comments', 'likes']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"Table {table}: {count} rows")
            
            # Check some foreign key relationships
            cursor.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE author_id NOT IN (SELECT id FROM users)
            """)
            orphaned_posts = cursor.fetchone()[0]
            logger.info(f"Orphaned posts (no author): {orphaned_posts}")
            
            cursor.execute("""
                SELECT COUNT(*) FROM comments 
                WHERE author_id NOT IN (SELECT id FROM users) 
                OR post_id NOT IN (SELECT id FROM posts)
            """)
            orphaned_comments = cursor.fetchone()[0]
            logger.info(f"Orphaned comments: {orphaned_comments}")
            
        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
    
    def convert(self) -> None:
        """Main conversion method"""
        try:
            logger.info("Starting database conversion...")
            
            # Connect to both databases
            self.connect_to_postgres()
            self.connect_to_sqlite()
            
            # Create tables in SQLite
            self.create_tables()
            
            # Copy data in the correct order
            self.copy_data_with_relationships()
            
            # Verify data integrity
            self.verify_data_integrity()
            
            logger.info("Database conversion completed successfully!")
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise
        finally:
            # Close connections
            if self.pg_conn:
                self.pg_conn.close()
                logger.info("Closed PostgreSQL connection")
            if self.sqlite_conn:
                self.sqlite_conn.close()
                logger.info("Closed SQLite connection")
    
    def cleanup(self) -> None:
        """Clean up SQLite database file if conversion fails"""
        if os.path.exists(self.sqlite_path):
            os.remove(self.sqlite_path)
            logger.info(f"Cleaned up SQLite file: {self.sqlite_path}")

def main():
    url = os.environ.get("REMOTE_CTRACK_DB_URL_1")
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    output = os.path.join(parent_dir, "app.db")

    converter = SupabaseToSQLiteConverter(url, output)

    try:
        converter.convert()
        logger.info(f"Successfully created SQLite database at: {output}")
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()