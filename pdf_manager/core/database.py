import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from ..utils.logging import DatabaseError

SCHEMA_VERSION = 1

class Database:
    def __init__(self, db_path: str):
        """Initialize database connection and ensure schema is created."""
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.connect()
        self.init_schema()

    def connect(self) -> None:
        """Establish database connection with proper settings."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # Enable foreign key support
            self.conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")

    def init_schema(self) -> None:
        """Initialize database schema if it doesn't exist."""
        try:
            with self.conn:
                # Version tracking
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        updated_at TIMESTAMP NOT NULL
                    )
                """)

                # Check current version
                cur = self.conn.execute("SELECT version FROM schema_version")
                version = cur.fetchone()
                if version and version[0] >= SCHEMA_VERSION:
                    return

                # Create tables
                self.conn.executescript("""
                    -- Documents table
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY,
                        filename TEXT NOT NULL,
                        path TEXT NOT NULL,
                        hash TEXT NOT NULL,
                        content_summary TEXT,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    );

                    -- Metadata table
                    CREATE TABLE IF NOT EXISTS metadata (
                        id INTEGER PRIMARY KEY,
                        document_id INTEGER NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id)
                    );

                    -- Tags table
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE
                    );

                    -- Document tags relationship
                    CREATE TABLE IF NOT EXISTS document_tags (
                        document_id INTEGER NOT NULL,
                        tag_id INTEGER NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id),
                        FOREIGN KEY (tag_id) REFERENCES tags(id),
                        PRIMARY KEY (document_id, tag_id)
                    );

                    -- LLM Processing table
                    CREATE TABLE IF NOT EXISTS llm_processing (
                        id INTEGER PRIMARY KEY,
                        document_id INTEGER NOT NULL,
                        operation TEXT NOT NULL,
                        model_used TEXT NOT NULL,
                        result TEXT NOT NULL,
                        tokens_used INTEGER,
                        processed_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id)
                    );

                    -- LLM Cache table
                    CREATE TABLE IF NOT EXISTS llm_cache (
                        id INTEGER PRIMARY KEY,
                        request_hash TEXT NOT NULL UNIQUE,
                        response TEXT NOT NULL,
                        tokens_used INTEGER,
                        model_used TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL
                    );

                    -- Create indexes
                    CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(hash);
                    CREATE INDEX IF NOT EXISTS idx_metadata_document_id ON metadata(document_id);
                    CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id);
                    CREATE INDEX IF NOT EXISTS idx_llm_processing_document_id ON llm_processing(document_id);
                    CREATE INDEX IF NOT EXISTS idx_llm_cache_request_hash ON llm_cache(request_hash);
                """)

                # Update schema version
                self.conn.execute(
                    "INSERT INTO schema_version (version, updated_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, datetime.utcnow())
                )

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database schema: {e}")

    def add_document(self, filename: str, path: str, hash: str, content_summary: Optional[str] = None) -> int:
        """Add a new document to the database."""
        try:
            with self.conn:
                cur = self.conn.execute("""
                    INSERT INTO documents (filename, path, hash, content_summary, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (filename, path, hash, content_summary, datetime.utcnow(), datetime.utcnow()))
                return cur.lastrowid
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to add document: {e}")

    def update_document(self, doc_id: int, updates: Dict[str, Any]) -> None:
        """Update document fields."""
        valid_fields = {'filename', 'path', 'content_summary'}
        update_fields = {k: v for k, v in updates.items() if k in valid_fields}
        
        if not update_fields:
            return

        try:
            with self.conn:
                fields = ', '.join(f"{k} = ?" for k in update_fields)
                values = list(update_fields.values())
                values.append(datetime.utcnow())
                values.append(doc_id)
                
                self.conn.execute(
                    f"UPDATE documents SET {fields}, updated_at = ? WHERE id = ?",
                    values
                )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update document: {e}")

    def add_metadata(self, doc_id: int, metadata: Dict[str, str]) -> None:
        """Add metadata for a document."""
        try:
            with self.conn:
                self.conn.executemany(
                    "INSERT INTO metadata (document_id, key, value) VALUES (?, ?, ?)",
                    [(doc_id, k, v) for k, v in metadata.items()]
                )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to add metadata: {e}")

    def add_tags(self, doc_id: int, tags: List[str]) -> None:
        """Add tags to a document, creating new tags if necessary."""
        try:
            with self.conn:
                # Insert new tags if they don't exist
                self.conn.executemany(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                    [(tag,) for tag in tags]
                )
                
                # Get tag IDs
                tag_ids = []
                for tag in tags:
                    cur = self.conn.execute("SELECT id FROM tags WHERE name = ?", (tag,))
                    tag_ids.append(cur.fetchone()[0])
                
                # Link tags to document
                self.conn.executemany(
                    "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                    [(doc_id, tag_id) for tag_id in tag_ids]
                )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to add tags: {e}")

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID with its metadata and tags."""
        try:
            with self.conn:
                # Get document
                cur = self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                doc = cur.fetchone()
                if not doc:
                    return None

                result = dict(doc)

                # Get metadata
                cur = self.conn.execute(
                    "SELECT key, value FROM metadata WHERE document_id = ?",
                    (doc_id,)
                )
                result['metadata'] = {row['key']: row['value'] for row in cur}

                # Get tags
                cur = self.conn.execute("""
                    SELECT t.name
                    FROM tags t
                    JOIN document_tags dt ON dt.tag_id = t.id
                    WHERE dt.document_id = ?
                """, (doc_id,))
                result['tags'] = [row['name'] for row in cur]

                return result
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get document: {e}")

    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """Search documents by content summary, metadata, or tags."""
        try:
            with self.conn:
                cur = self.conn.execute("""
                    SELECT DISTINCT d.*
                    FROM documents d
                    LEFT JOIN metadata m ON d.id = m.document_id
                    LEFT JOIN document_tags dt ON d.id = dt.document_id
                    LEFT JOIN tags t ON dt.tag_id = t.id
                    WHERE d.content_summary LIKE ?
                    OR d.filename LIKE ?
                    OR m.value LIKE ?
                    OR t.name LIKE ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
                
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to search documents: {e}")

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
