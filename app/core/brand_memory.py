"""
Brand Memory System - RAG for Design Intelligence

This module works with YOUR existing schema (UUID-based with organizations)
to store and retrieve brand knowledge.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from uuid import UUID
from openai import OpenAI

from app.infra.config import settings
from app.infra.db import get_db

# Add UUIDEncoder for safe JSON serialization of UUIDs
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        from uuid import UUID
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class BrandMemory:
    """Manages brand memory and retrieval for intelligent design decisions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # ==================== STORE DESIGN HISTORY ====================
    
    def store_design(
        self,
        org_id: UUID,
        asset_id: UUID,
        design_type: str,
        platform: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        layout_type: Optional[str] = None,
        colors_used: Optional[List[str]] = None,
        fonts_used: Optional[List[str]] = None,
        text_content: Optional[str] = None
    ) -> UUID:
        """
        Store a design in memory with embeddings for future retrieval
        
        Args:
            org_id: Organization UUID
            asset_id: Reference to assets table
            design_type: Type of design (social_post, ad, banner, story)
            platform: Target platform (instagram, facebook, etc.)
            aspect_ratio: Image dimensions
            layout_type: Layout style used
            colors_used: List of hex colors
            fonts_used: List of font names
            text_content: Any text in the design
        
        Returns:
            design_history UUID
        """
        # Create searchable description for embedding
        description = self._create_design_description(
            design_type=design_type,
            platform=platform,
            layout_type=layout_type,
            colors_used=colors_used or [],
            text_content=text_content
        )
        
        # Generate embedding
        embedding = self._generate_embedding(description)
        
        # Store in database
        db = get_db()

        query = """
            INSERT INTO design_history (
                org_id, asset_id, design_type, platform, aspect_ratio,
                layout_type, colors_used, fonts_used, has_logo, has_text,
                text_content, embedding, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        result = db.fetch_one(query, (
            str(org_id), str(asset_id), design_type, platform, aspect_ratio,
            layout_type, json.dumps(colors_used or [], cls=UUIDEncoder), json.dumps(fonts_used or [], cls=UUIDEncoder),
            True, bool(text_content), text_content,
            f'[{",".join(map(str, embedding))}]', datetime.now()
        ))

        design_id = result['id']

        return design_id
    
    # ==================== RETRIEVE SIMILAR DESIGNS ====================
    
    def find_similar_designs(
        self,
        org_id: UUID,
        query: str,
        design_type: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar past designs using semantic search
        
        Args:
            org_id: Organization UUID
            query: Natural language query
            design_type: Filter by design type
            platform: Filter by platform
            limit: Max results to return
        
        Returns:
            List of similar designs with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Build SQL query with filters
        sql = """
            SELECT 
                id, design_type, platform, aspect_ratio, layout_type,
                colors_used, fonts_used, text_content, created_at,
                1 - (embedding <=> %s::vector) as similarity_score
            FROM design_history
            WHERE org_id = %s
        """
        
        params = [f'[{",".join(map(str, query_embedding))}]', str(org_id)]
        
        if design_type:
            sql += " AND design_type = %s"
            params.append(design_type)
        
        if platform:
            sql += " AND platform = %s"
            params.append(platform)
        
        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([f'[{",".join(map(str, query_embedding))}]', limit])

        db = get_db()
        rows = db.fetch_all(sql, tuple(params))

        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'design_type': row['design_type'],
                'platform': row['platform'],
                'aspect_ratio': row['aspect_ratio'],
                'layout_type': row['layout_type'],
                'colors_used': row['colors_used'],
                'fonts_used': row['fonts_used'],
                'text_content': row['text_content'],
                'created_at': row['created_at'],
                'similarity_score': row['similarity_score']
            })

        return results
    
    # ==================== FEEDBACK & LEARNING ====================
    
    def record_feedback(
        self,
        design_id: UUID,
        org_id: UUID,
        user_id: UUID,
        feedback_type: str,
        rating: Optional[int] = None,
        what_worked: Optional[str] = None,
        what_failed: Optional[str] = None,
        revision_notes: Optional[str] = None
    ) -> UUID:
        """
        Record user feedback on a design
        
        Args:
            design_id: Reference to design_history
            org_id: Organization UUID
            user_id: User UUID
            feedback_type: 'approved', 'rejected', 'revised'
            rating: 1-5 rating
            what_worked: Positive feedback
            what_failed: Negative feedback
            revision_notes: Specific changes requested
        
        Returns:
            feedback UUID
        """
        db = get_db()

        query = """
            INSERT INTO design_feedback (
                design_id, org_id, user_id, feedback_type, rating,
                what_worked, what_failed, revision_notes, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        result = db.fetch_one(query, (
            str(design_id), str(org_id), str(user_id), feedback_type, rating,
            what_worked, what_failed, revision_notes, datetime.now()
        ))

        feedback_id = result['id']

        # Trigger pattern learning
        self._update_patterns_from_feedback(org_id, design_id, feedback_type)

        return feedback_id
    
    # ==================== PATTERN LEARNING ====================
    
    def get_brand_patterns(
        self,
        org_id: UUID,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.3
    ) -> List[Dict]:
        """
        Get learned patterns for an organization
        
        Args:
            org_id: Organization UUID
            pattern_type: Filter by pattern type
            min_confidence: Minimum confidence score
        
        Returns:
            List of learned patterns
        """
        db = get_db()

        query = """
            SELECT pattern_type, pattern_name, pattern_value,
                   confidence_score, sample_count
            FROM brand_patterns
            WHERE org_id = %s AND confidence_score >= %s
        """

        params = [str(org_id), min_confidence]

        if pattern_type:
            query += " AND pattern_type = %s"
            params.append(pattern_type)

        query += " ORDER BY confidence_score DESC"

        rows = db.fetch_all(query, tuple(params))

        patterns = []
        for row in rows:
            patterns.append({
                'pattern_type': row['pattern_type'],
                'pattern_name': row['pattern_name'],
                'pattern_value': row['pattern_value'],
                'confidence_score': row['confidence_score'],
                'sample_count': row['sample_count']
            })

        return patterns
    
    def _update_patterns_from_feedback(
        self,
        org_id: UUID,
        design_id: UUID,
        feedback_type: str
    ):
        """Analyze feedback and update learned patterns"""

        db = get_db()

        # Get design details
        design = db.fetch_one("""
            SELECT layout_type, colors_used, design_type, platform
            FROM design_history WHERE id = %s
        """, (str(design_id),))

        if not design:
            return

        layout_type = design['layout_type']
        design_type = design['design_type']

        # Update layout preference pattern
        if feedback_type == 'approved' and layout_type:
            self._upsert_pattern(
                org_id=org_id,
                pattern_type='layout_preference',
                pattern_name=f'{design_type}_{layout_type}',
                pattern_value={'layout': layout_type, 'design_type': design_type},
                design_id=design_id
            )
    
    def _upsert_pattern(
        self,
        org_id: UUID,
        pattern_type: str,
        pattern_name: str,
        pattern_value: Dict,
        design_id: UUID
    ):
        """Insert or update a learned pattern"""

        db = get_db()

        # Check if pattern exists
        existing = db.fetch_one("""
            SELECT id, sample_count, confidence_score, example_design_ids
            FROM brand_patterns
            WHERE org_id = %s AND pattern_type = %s AND pattern_name = %s
        """, (str(org_id), pattern_type, pattern_name))

        if existing:
            # Update existing pattern
            pattern_id = existing['id']
            sample_count = existing['sample_count']
            confidence = existing['confidence_score']
            examples = existing['example_design_ids']

            new_count = sample_count + 1
            new_confidence = min(1.0, confidence + 0.05)  # Increase confidence
            new_examples = (examples or []) + [str(design_id)]

            db.update(
                table='brand_patterns',
                data={
                    'sample_count': new_count,
                    'confidence_score': new_confidence,
                    'example_design_ids': new_examples,
                    'updated_at': datetime.now()
                },
                where_clause='id = %s',
                where_params=(pattern_id,)
            )
        else:
            # Create new pattern
            db.insert(
                table='brand_patterns',
                data={
                    'org_id': str(org_id),
                    'pattern_type': pattern_type,
                    'pattern_name': pattern_name,
                    'pattern_value': json.dumps(pattern_value, cls=UUIDEncoder),
                    'confidence_score': 0.3,
                    'sample_count': 1,
                    'example_design_ids': [str(design_id)]
                }
            )
    
    # ==================== UTILITIES ====================
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def _create_design_description(
        self,
        design_type: str,
        platform: Optional[str],
        layout_type: Optional[str],
        colors_used: List[str],
        text_content: Optional[str]
    ) -> str:
        """Create searchable description from design attributes"""
        parts = [
            f"Design type: {design_type}",
            f"Platform: {platform or 'general'}",
            f"Layout: {layout_type or 'standard'}",
            f"Colors: {', '.join(colors_used) if colors_used else 'brand colors'}",
        ]
        
        if text_content:
            parts.append(f"Text: {text_content}")
        
        return ". ".join(parts)
    
    # ==================== BRAND CONTEXT ====================
    
    def get_brand_context(self, org_id: UUID, query: str) -> Dict[str, Any]:
        """
        Get comprehensive brand context for a design request
        
        Returns:
            Dictionary with:
            - similar_designs: Past similar work
            - patterns: Learned preferences
            - stats: Brand statistics
        """
        return {
            'similar_designs': self.find_similar_designs(org_id, query, limit=3),
            'patterns': self.get_brand_patterns(org_id),
            'stats': self._get_brand_stats(org_id)
        }
    
    def _get_brand_stats(self, org_id: UUID) -> Dict:
        """Get quick stats about brand history"""
        db = get_db()

        stats = db.fetch_one("""
            SELECT COUNT(*) as total_designs,
                   COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as recent_designs
            FROM design_history
            WHERE org_id = %s
        """, (str(org_id),))

        return {
            'total_designs': stats['total_designs'] if stats else 0,
            'recent_designs': stats['recent_designs'] if stats else 0
        }


# Singleton instance
brand_memory = BrandMemory()