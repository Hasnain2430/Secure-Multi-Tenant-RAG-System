"""
retrieval/index.py - Index Builder and Retriever with LangChain integration
"""
from __future__ import annotations
import os
import csv
from dataclasses import dataclass
from typing import List

# Disable telemetry BEFORE importing chromadb
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = '1'
os.environ['CHROMADB_ALLOW_TELEMETRY'] = 'false'

from sentence_transformers import SentenceTransformer
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class Hit:
    """Search result with metadata"""
    doc_id: str
    tenant: str
    visibility: str
    text: str
    score: float
    pii_flag: bool = False
    path: str = ""


def load_manifest(base_dir: str) -> list[dict]:
    """Load data/manifest.csv"""
    mpath = os.path.join(base_dir, "data", "manifest.csv")
    with open(mpath, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_acl(base_dir: str) -> dict:
    """Load data/tenant_acl.csv"""
    acl_path = os.path.join(base_dir, "data", "tenant_acl.csv")
    acl = {}
    if os.path.exists(acl_path):
        with open(acl_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get("doc_id", "")
                tenant_id = row.get("tenant_id", "")
                # Normalize tenant ID to base (U1, U2, U3, U4, or public)
                if tenant_id.startswith("U1"):
                    tenant = "U1"
                elif tenant_id.startswith("U2"):
                    tenant = "U2"
                elif tenant_id.startswith("U3"):
                    tenant = "U3"
                elif tenant_id.startswith("U4"):
                    tenant = "U4"
                elif tenant_id == "PUB":
                    tenant = "public"
                else:
                    tenant = tenant_id
                visibility = row.get("visibility", "private")
                acl[doc_id] = {"tenant": tenant, "visibility": visibility}
    return acl


def read_doc(base_dir: str, rel_path: str) -> str:
    """Read document content"""
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        with open(full_path, encoding="utf-8") as f:
            return f.read()
    return ""


def build_or_update(base_dir: str):
    """
    Idempotently build per-tenant indices using Chroma + LangChain text splitter.
    
    This function:
    1. Reads manifest.csv and tenant_acl.csv
    2. Chunks documents using LangChain RecursiveCharacterTextSplitter
    3. Creates/updates per-tenant collections in Chroma
    4. Is idempotent - repeated calls won't duplicate data (uses upsert)
    """
    manifest = load_manifest(base_dir)
    acl = load_acl(base_dir)
    
    # Initialize Chroma client
    chroma_path = os.path.join(base_dir, ".chroma")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Initialize LangChain text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    # Group by tenant (normalize tenant names to base U1, U2, U3, U4, or public)
    by_tenant = {}
    for row in manifest:
        tenant = row["tenant"]
        if tenant == "PUB":
            tenant = "public"
        elif tenant.startswith("U1"):
            tenant = "U1"
        elif tenant.startswith("U2"):
            tenant = "U2"
        elif tenant.startswith("U3"):
            tenant = "U3"
        elif tenant.startswith("U4"):
            tenant = "U4"
        by_tenant.setdefault(tenant, []).append(row)
    
    # Index each tenant
    for tenant, rows in by_tenant.items():
        collection_name = f"tenant_{tenant}"
        coll = client.get_or_create_collection(name=collection_name)
        
        ids = []
        documents = []
        metadatas = []
        
        for row in rows:
            doc_id = row["doc_id"]
            path = row["path"]
            
            # Read document
            content = read_doc(base_dir, path)
            if not content:
                continue
            
            # Chunk using LangChain
            chunks = text_splitter.split_text(content)
            
            # Determine visibility and normalize tenant
            if doc_id in acl:
                doc_tenant = acl[doc_id]["tenant"]
                visibility = acl[doc_id]["visibility"]
            else:
                doc_tenant = tenant  # Already normalized in the grouping step
                visibility = "public" if (tenant == "public" or "PUB_" in doc_id) else "private"
            
            # Add chunks
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{chunk_idx}"
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({
                    "doc_id": doc_id,
                    "tenant": doc_tenant,
                    "visibility": visibility,
                    "path": path,
                    "pii": False
                })
        
        # Upsert (idempotent)
        if ids:
            coll.upsert(ids=ids, documents=documents, metadatas=metadatas)


def search(query: str, tenant_id: str, top_k: int = 6) -> List[Hit]:
    """
    Search across tenant's namespace and public namespace.
    
    Args:
        query: Search query string
        tenant_id: Active tenant (U1, U2, U3, U4)
        top_k: Number of results to return
        
    Returns:
        List of Hit objects with metadata
    """
    # Get base directory
    import sys
    if hasattr(sys.modules['__main__'], '__file__'):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)))
    else:
        base_dir = os.getcwd()
    
    chroma_path = os.path.join(base_dir, ".chroma")
    client = chromadb.PersistentClient(path=chroma_path)
    
    hits: List[Hit] = []
    
    def query_namespace(ns: str):
        """Query a specific namespace"""
        try:
            coll = client.get_collection(ns)
            res = coll.query(query_texts=[query], n_results=top_k)
            
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            dists = res.get("distances", [[]])[0]
            
            for text, meta, dist in zip(docs, metas, dists):
                score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.5
                
                hits.append(Hit(
                    doc_id=meta.get("doc_id", ""),
                    tenant=meta.get("tenant", ""),
                    visibility=meta.get("visibility", "private"),
                    text=text,
                    score=score,
                    pii_flag=meta.get("pii", False),
                    path=meta.get("path", "")
                ))
        except Exception:
            # Collection doesn't exist
            pass
    
    # Query tenant and public namespaces
    query_namespace(f"tenant_{tenant_id}")
    query_namespace("tenant_public")
    
    # Sort by score and return top_k
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]
