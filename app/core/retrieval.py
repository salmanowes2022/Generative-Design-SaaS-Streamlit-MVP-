"""
Brand Corpus Retrieval
Handles embedding generation, ingestion, and semantic search
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import io
import zipfile
from datetime import datetime
import numpy as np
from PIL import Image
import PyPDF2
from openai import OpenAI

from app.infra.config import settings
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text and images"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.text_model = "text-embedding-ada-002"
        self.embedding_dim = 1536
    
    def generate_text_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI ada-002
        
        Args:
            text: Input text
        
        Returns:
            List of floats (dimension 1536)
        """
        try:
            response = self.client.embeddings.create(
                model=self.text_model,
                input=text
            )
            embedding = response.data[0].embedding
            logger.info(f"Generated text embedding (dim={len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating text embedding: {str(e)}")
            raise
    
    def generate_image_embedding(self, image: Image.Image) -> List[float]:
        """
        Generate embedding for image using CLIP (via OpenAI or fallback)
        
        For MVP: Use image description → text embedding
        For Production: Use actual CLIP model
        
        Args:
            image: PIL Image
        
        Returns:
            List of floats (dimension 1536)
        """
        try:
            # MVP: Generate description and embed it
            # In production, use actual CLIP: https://github.com/openai/CLIP
            description = self._describe_image(image)
            return self.generate_text_embedding(description)
            
        except Exception as e:
            logger.error(f"Error generating image embedding: {str(e)}")
            raise
    
    def _describe_image(self, image: Image.Image) -> str:
        """
        Generate text description of image
        For MVP: Use basic attributes
        For Production: Use Vision API
        """
        # Basic image features
        width, height = image.size
        aspect = width / height
        mode = image.mode
        
        # Simple description
        desc = f"Image {width}x{height}px, aspect {aspect:.2f}, mode {mode}"
        
        # Could enhance with dominant colors, etc.
        return desc


class CorpusIngestion:
    """Handles ingestion of brand corpus from ZIP files"""
    
    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
    
    def ingest_zip(
        self,
        org_id: UUID,
        brand_kit_id: UUID,
        zip_data: bytes,
        channel: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Ingest brand corpus from ZIP file
        
        Expected structure:
        - images/ (PNG, JPG)
        - pdfs/ (PDF documents)
        - captions.txt or captions.json
        
        Args:
            org_id: Organization ID
            brand_kit_id: Brand kit ID
            zip_data: ZIP file bytes
            channel: Optional channel tag
        
        Returns:
            Dict with counts: {images: n, texts: n, pdfs: n}
        """
        counts = {"images": 0, "texts": 0, "pdfs": 0}
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                for file_info in zf.filelist:
                    if file_info.is_dir():
                        continue
                    
                    file_path = Path(file_info.filename)
                    file_ext = file_path.suffix.lower()
                    
                    # Process images
                    if file_ext in ['.png', '.jpg', '.jpeg']:
                        with zf.open(file_info) as f:
                            self._ingest_image(
                                org_id, brand_kit_id, f.read(),
                                file_path.name, channel
                            )
                            counts["images"] += 1
                    
                    # Process PDFs
                    elif file_ext == '.pdf':
                        with zf.open(file_info) as f:
                            self._ingest_pdf(
                                org_id, brand_kit_id, f.read(),
                                file_path.name, channel
                            )
                            counts["pdfs"] += 1
                    
                    # Process text files
                    elif file_ext in ['.txt', '.md']:
                        with zf.open(file_info) as f:
                            self._ingest_text(
                                org_id, brand_kit_id, f.read().decode('utf-8'),
                                file_path.name, channel
                            )
                            counts["texts"] += 1
            
            logger.info(f"Ingested ZIP: {counts}")
            return counts
            
        except Exception as e:
            logger.error(f"Error ingesting ZIP: {str(e)}")
            raise
    
    def _ingest_image(
        self,
        org_id: UUID,
        brand_kit_id: UUID,
        image_data: bytes,
        filename: str,
        channel: Optional[str]
    ) -> None:
        """Ingest single image"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Generate embedding
            embedding = self.embedding_gen.generate_image_embedding(image)
            
            # Detect aspect ratio
            w, h = image.size
            aspect = self._classify_aspect_ratio(w, h)
            
            # Store embedding
            db.insert("asset_embeddings", {
                "org_id": str(org_id),
                "brand_kit_id": str(brand_kit_id),
                "kind": "image",
                "channel": channel,
                "aspect_ratio": aspect,
                "content": f"Image: {filename}",
                "embedding": f"[{','.join(map(str, embedding))}]",
                "meta": f'{{"filename": "{filename}", "size": [{w}, {h}]}}'
            })
            
            logger.debug(f"Ingested image: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to ingest image {filename}: {str(e)}")
    
    def _ingest_pdf(
        self,
        org_id: UUID,
        brand_kit_id: UUID,
        pdf_data: bytes,
        filename: str,
        channel: Optional[str]
    ) -> None:
        """Ingest PDF and extract text"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            
            # Extract text from all pages
            text_chunks = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_chunks.append(text.strip())
            
            # Combine and generate embedding
            full_text = " ".join(text_chunks)
            if len(full_text) < 10:
                logger.warning(f"PDF {filename} has minimal text, skipping")
                return
            
            embedding = self.embedding_gen.generate_text_embedding(full_text)
            
            # Store embedding
            db.insert("asset_embeddings", {
                "org_id": str(org_id),
                "brand_kit_id": str(brand_kit_id),
                "kind": "pdf_text",
                "channel": channel,
                "content": full_text[:500],  # Store preview
                "embedding": f"[{','.join(map(str, embedding))}]",
                "meta": f'{{"filename": "{filename}", "pages": {len(pdf_reader.pages)}}}'
            })
            
            logger.debug(f"Ingested PDF: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to ingest PDF {filename}: {str(e)}")
    
    def _ingest_text(
        self,
        org_id: UUID,
        brand_kit_id: UUID,
        text: str,
        filename: str,
        channel: Optional[str]
    ) -> None:
        """Ingest plain text"""
        try:
            if len(text.strip()) < 10:
                return
            
            embedding = self.embedding_gen.generate_text_embedding(text)
            
            db.insert("asset_embeddings", {
                "org_id": str(org_id),
                "brand_kit_id": str(brand_kit_id),
                "kind": "text",
                "channel": channel,
                "content": text[:500],
                "embedding": f"[{','.join(map(str, embedding))}]",
                "meta": f'{{"filename": "{filename}"}}'
            })
            
            logger.debug(f"Ingested text: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to ingest text {filename}: {str(e)}")
    
    def _classify_aspect_ratio(self, width: int, height: int) -> str:
        """Classify image aspect ratio"""
        ratio = width / height
        
        if 0.95 <= ratio <= 1.05:
            return "1:1"
        elif 0.75 <= ratio <= 0.85:
            return "4:5"
        elif 0.50 <= ratio <= 0.60:
            return "9:16"
        elif 1.75 <= ratio <= 1.80:
            return "16:9"
        else:
            return f"{width}:{height}"


class BrandRetrieval:
    """Semantic search over brand corpus"""
    
    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
    
    def search_similar(
        self,
        brand_kit_id: UUID,
        query: str,
        kind: Optional[str] = None,
        channel: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar assets in brand corpus
        
        Args:
            brand_kit_id: Brand kit to search within
            query: Text query to embed and search
            kind: Filter by kind (image, text, pdf_text, caption)
            channel: Filter by channel
            aspect_ratio: Filter by aspect ratio
            top_k: Number of results to return
        
        Returns:
            List of dicts with {content, similarity, meta, kind, channel}
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_gen.generate_text_embedding(query)
            query_vec = f"[{','.join(map(str, query_embedding))}]"
            
            # Build filter conditions
            filters = [f"brand_kit_id = '{brand_kit_id}'"]
            if kind:
                filters.append(f"kind = '{kind}'")
            if channel:
                filters.append(f"channel = '{channel}'")
            if aspect_ratio:
                filters.append(f"aspect_ratio = '{aspect_ratio}'")
            
            where_clause = " AND ".join(filters)
            
            # Cosine similarity search using pgvector
            query = f"""
                SELECT 
                    content,
                    kind,
                    channel,
                    aspect_ratio,
                    meta,
                    1 - (embedding <=> '{query_vec}'::vector) as similarity
                FROM asset_embeddings
                WHERE {where_clause}
                ORDER BY embedding <=> '{query_vec}'::vector
                LIMIT {top_k}
            """
            
            results = db.fetch_all(query)
            
            # Parse meta (handle both string and dict)
            parsed_results = []
            for r in results:
                meta_data = r.get("meta", {})
                if isinstance(meta_data, str):
                    import json
                    meta_data = json.loads(meta_data)
                
                parsed_results.append({
                    "content": r["content"],
                    "kind": r["kind"],
                    "channel": r.get("channel"),
                    "aspect_ratio": r.get("aspect_ratio"),
                    "similarity": float(r["similarity"]),
                    "meta": meta_data
                })
            
            logger.info(f"Found {len(parsed_results)} similar assets")
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error searching similar assets: {str(e)}")
            # Return empty list on error rather than crash
            return []


# Global instances
embedding_generator = EmbeddingGenerator()
corpus_ingestion = CorpusIngestion()
brand_retrieval = BrandRetrieval()