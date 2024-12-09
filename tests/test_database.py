import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
from pdf_manager.core.database import Database
from pdf_manager.utils.logging import DatabaseError

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    yield db
    db.close()

def test_database_initialization(temp_db):
    """Test database initialization and schema creation."""
    # Check if tables exist
    tables = [
        'documents',
        'metadata',
        'tags',
        'document_tags',
        'llm_processing',
        'llm_cache'
    ]
    
    for table in tables:
        cur = temp_db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        assert cur.fetchone() is not None

def test_add_document(temp_db):
    """Test adding a document to the database."""
    doc_id = temp_db.add_document(
        filename="test.pdf",
        path="/path/to/test.pdf",
        hash="123456",
        content_summary="Test document"
    )
    
    # Verify document was added
    cur = temp_db.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cur.fetchone()
    assert doc['filename'] == "test.pdf"
    assert doc['hash'] == "123456"

def test_add_metadata(temp_db):
    """Test adding metadata to a document."""
    # Add document first
    doc_id = temp_db.add_document(
        filename="test.pdf",
        path="/path/to/test.pdf",
        hash="123456"
    )
    
    # Add metadata
    metadata = {
        'title': 'Test Document',
        'author': 'Test Author',
        'pages': '10'
    }
    temp_db.add_metadata(doc_id, metadata)
    
    # Verify metadata
    cur = temp_db.conn.execute("SELECT * FROM metadata WHERE document_id = ?", (doc_id,))
    results = {row['key']: row['value'] for row in cur}
    assert results == metadata

def test_add_tags(temp_db):
    """Test adding tags to a document."""
    # Add document
    doc_id = temp_db.add_document(
        filename="test.pdf",
        path="/path/to/test.pdf",
        hash="123456"
    )
    
    # Add tags
    tags = ['important', 'test', 'document']
    temp_db.add_tags(doc_id, tags)
    
    # Verify tags
    cur = temp_db.conn.execute("""
        SELECT t.name
        FROM tags t
        JOIN document_tags dt ON t.id = dt.tag_id
        WHERE dt.document_id = ?
    """, (doc_id,))
    
    result_tags = [row['name'] for row in cur]
    assert sorted(result_tags) == sorted(tags)

def test_get_document(temp_db):
    """Test retrieving a document with its metadata and tags."""
    # Add document with metadata and tags
    doc_id = temp_db.add_document(
        filename="test.pdf",
        path="/path/to/test.pdf",
        hash="123456",
        content_summary="Test content"
    )
    
    metadata = {'title': 'Test', 'author': 'Author'}
    tags = ['tag1', 'tag2']
    
    temp_db.add_metadata(doc_id, metadata)
    temp_db.add_tags(doc_id, tags)
    
    # Retrieve document
    doc = temp_db.get_document(doc_id)
    
    assert doc['filename'] == "test.pdf"
    assert doc['hash'] == "123456"
    assert doc['metadata'] == metadata
    assert sorted(doc['tags']) == sorted(tags)

def test_search_documents(temp_db):
    """Test document search functionality."""
    # Add test documents
    docs = [
        {
            'filename': 'test1.pdf',
            'path': '/path/to/test1.pdf',
            'hash': '111',
            'content_summary': 'This is a test document about Python'
        },
        {
            'filename': 'test2.pdf',
            'path': '/path/to/test2.pdf',
            'hash': '222',
            'content_summary': 'This is a document about Java'
        }
    ]
    
    for doc in docs:
        doc_id = temp_db.add_document(**doc)
        if 'Python' in doc['content_summary']:
            temp_db.add_tags(doc_id, ['programming', 'python'])
        else:
            temp_db.add_tags(doc_id, ['programming', 'java'])
    
    # Search by content
    python_docs = temp_db.search_documents('Python')
    assert len(python_docs) == 1
    assert python_docs[0]['hash'] == '111'
    
    # Search by tag
    programming_docs = temp_db.search_documents('programming')
    assert len(programming_docs) == 2

def test_invalid_document_id(temp_db):
    """Test handling of invalid document ID."""
    with pytest.raises(DatabaseError):
        temp_db.add_metadata(999, {'key': 'value'})

def test_duplicate_tags(temp_db):
    """Test handling of duplicate tags."""
    doc_id = temp_db.add_document(
        filename="test.pdf",
        path="/path/to/test.pdf",
        hash="123456"
    )
    
    # Add same tags twice
    tags = ['tag1', 'tag2']
    temp_db.add_tags(doc_id, tags)
    temp_db.add_tags(doc_id, tags)
    
    # Verify no duplicates
    cur = temp_db.conn.execute("""
        SELECT COUNT(*) as count
        FROM document_tags
        WHERE document_id = ?
    """, (doc_id,))
    
    assert cur.fetchone()['count'] == len(tags) 