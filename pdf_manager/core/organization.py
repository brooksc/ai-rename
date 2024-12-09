import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from ..utils.logging import ProcessingError
from ..core.database import Database

class DocumentOrganizer:
    def __init__(self, config: Dict[str, Any], db: Database):
        """Initialize document organizer with configuration and database connection."""
        self.config = config
        self.db = db
        self.library_path = Path(config['paths']['library'])
        self.backup_path = Path(config['paths']['backup'])
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        try:
            self.library_path.mkdir(parents=True, exist_ok=True)
            self.backup_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ProcessingError(f"Failed to create required directories: {e}")

    def organize_document(self, doc_id: int, source_path: str,
                        categories: List[str], tags: List[str]) -> str:
        """
        Organize a document in the library based on its categories and tags.
        
        Args:
            doc_id: Database ID of the document
            source_path: Current path of the document
            categories: List of categories for organization
            tags: List of tags to apply
            
        Returns:
            str: New path of the document in the library
        """
        try:
            # Create category-based path
            relative_path = self._build_category_path(categories)
            target_dir = self.library_path / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename
            source_file = Path(source_path)
            target_path = self._get_unique_path(target_dir, source_file.name)

            # Backup existing file if it's being moved
            if os.path.exists(target_path):
                self._backup_file(target_path)

            # Move/copy file to new location
            shutil.copy2(source_path, target_path)

            # Update database
            self._update_document_location(doc_id, str(target_path))
            self._apply_tags(doc_id, tags)

            return str(target_path)

        except Exception as e:
            raise ProcessingError(f"Failed to organize document: {e}")

    def _build_category_path(self, categories: List[str]) -> Path:
        """Build relative path based on categories."""
        # Use only the first 2 categories to avoid deep nesting
        valid_categories = [self._sanitize_path(cat) for cat in categories[:2]]
        return Path(*valid_categories) if valid_categories else Path('uncategorized')

    def _sanitize_path(self, path_component: str) -> str:
        """Sanitize path component for safe filesystem use."""
        # Replace invalid characters and spaces
        sanitized = "".join(c if c.isalnum() else "_" for c in path_component.lower())
        return sanitized.strip("_")

    def _get_unique_path(self, directory: Path, filename: str) -> Path:
        """Generate unique path for file in directory."""
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        counter = 1
        target_path = directory / filename

        while target_path.exists():
            new_name = f"{base_name}_{counter}{extension}"
            target_path = directory / new_name
            counter += 1

        return target_path

    def _backup_file(self, file_path: Path) -> None:
        """Create backup of existing file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_path / backup_name
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            logging.warning(f"Failed to create backup of {file_path}: {e}")

    def _update_document_location(self, doc_id: int, new_path: str) -> None:
        """Update document location in database."""
        try:
            with self.db.conn:
                self.db.conn.execute("""
                    UPDATE documents
                    SET path = ?, updated_at = ?
                    WHERE id = ?
                """, (new_path, datetime.utcnow(), doc_id))
        except Exception as e:
            raise ProcessingError(f"Failed to update document location: {e}")

    def _apply_tags(self, doc_id: int, tags: List[str]) -> None:
        """Apply tags to document in database."""
        try:
            with self.db.conn:
                # Insert new tags
                self.db.conn.executemany(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                    [(tag,) for tag in tags]
                )

                # Get tag IDs
                tag_ids = []
                for tag in tags:
                    cur = self.db.conn.execute(
                        "SELECT id FROM tags WHERE name = ?",
                        (tag,)
                    )
                    if result := cur.fetchone():
                        tag_ids.append(result[0])

                # Link tags to document
                self.db.conn.executemany(
                    "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                    [(doc_id, tag_id) for tag_id in tag_ids]
                )
        except Exception as e:
            raise ProcessingError(f"Failed to apply tags: {e}")

    def reorganize_library(self) -> Dict[str, Any]:
        """
        Reorganize entire library based on current categories and tags.
        
        Returns:
            Dict with statistics about the reorganization
        """
        stats = {'processed': 0, 'failed': 0, 'skipped': 0}

        try:
            # Get all documents
            cur = self.db.conn.execute("""
                SELECT d.id, d.path, d.filename,
                       GROUP_CONCAT(DISTINCT t.name) as tags
                FROM documents d
                LEFT JOIN document_tags dt ON d.id = dt.document_id
                LEFT JOIN tags t ON dt.tag_id = t.id
                GROUP BY d.id
            """)

            for doc in cur.fetchall():
                try:
                    # Skip if file doesn't exist
                    if not os.path.exists(doc['path']):
                        stats['skipped'] += 1
                        continue

                    # Get categories from metadata
                    categories_cur = self.db.conn.execute("""
                        SELECT value
                        FROM metadata
                        WHERE document_id = ? AND key = 'categories'
                    """, (doc['id'],))
                    
                    if categories_result := categories_cur.fetchone():
                        categories = categories_result['value'].split(',')
                    else:
                        categories = ['uncategorized']

                    # Get tags
                    tags = doc['tags'].split(',') if doc['tags'] else []

                    # Reorganize document
                    self.organize_document(doc['id'], doc['path'], categories, tags)
                    stats['processed'] += 1

                except Exception as e:
                    logging.error(f"Failed to reorganize document {doc['path']}: {e}")
                    stats['failed'] += 1

        except Exception as e:
            raise ProcessingError(f"Failed to reorganize library: {e}")

        return stats

    def get_organization_stats(self) -> Dict[str, Any]:
        """Get statistics about library organization."""
        try:
            stats = {}

            # Get category distribution
            cur = self.db.conn.execute("""
                SELECT m.value as category, COUNT(*) as count
                FROM metadata m
                WHERE m.key = 'categories'
                GROUP BY m.value
                ORDER BY count DESC
            """)
            stats['categories'] = {row['category']: row['count'] for row in cur}

            # Get tag distribution
            cur = self.db.conn.execute("""
                SELECT t.name, COUNT(*) as count
                FROM tags t
                JOIN document_tags dt ON t.id = dt.tag_id
                GROUP BY t.name
                ORDER BY count DESC
            """)
            stats['tags'] = {row['name']: row['count'] for row in cur}

            # Get total documents and size
            cur = self.db.conn.execute("""
                SELECT COUNT(*) as total_docs,
                       COUNT(DISTINCT path) as unique_paths
                FROM documents
            """)
            stats.update(dict(cur.fetchone()))

            return stats

        except Exception as e:
            raise ProcessingError(f"Failed to get organization stats: {e}")

    def cleanup_missing_files(self) -> Dict[str, int]:
        """Remove database entries for missing files."""
        stats = {'removed': 0, 'errors': 0}

        try:
            cur = self.db.conn.execute("SELECT id, path FROM documents")
            for doc in cur:
                if not os.path.exists(doc['path']):
                    try:
                        with self.db.conn:
                            # Remove related entries
                            self.db.conn.execute("DELETE FROM metadata WHERE document_id = ?", (doc['id'],))
                            self.db.conn.execute("DELETE FROM document_tags WHERE document_id = ?", (doc['id'],))
                            self.db.conn.execute("DELETE FROM llm_processing WHERE document_id = ?", (doc['id'],))
                            self.db.conn.execute("DELETE FROM documents WHERE id = ?", (doc['id'],))
                        stats['removed'] += 1
                    except Exception as e:
                        logging.error(f"Failed to remove entries for {doc['path']}: {e}")
                        stats['errors'] += 1

        except Exception as e:
            raise ProcessingError(f"Failed to cleanup missing files: {e}")

        return stats
