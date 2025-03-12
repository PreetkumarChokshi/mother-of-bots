import hashlib
from typing import Optional, Dict

class Document:
    def __init__(self, content: str, metadata: Optional[Dict] = None):
        self.content = content
        self.metadata = metadata or {}
        unique_id = f"{self.metadata.get('source', 'unknown')}-{hashlib.sha256(content.encode()).hexdigest()[:10]}"
        self.id = hashlib.sha256(unique_id.encode()).hexdigest() 