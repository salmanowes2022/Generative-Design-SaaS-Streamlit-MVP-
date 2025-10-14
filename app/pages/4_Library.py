"""
Library Page
View and manage all generated assets
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime, timedelta
import json
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Asset Library", page_icon="📚", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"


def main():
    st.title("📚 Asset Library")
    st.markdown("Browse and manage your generated assets")
    
    # Filters
    st.subheader("🔍 Filters")
    
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        date_filter = st.selectbox(
            "Time Period",
            options=[
                ("All Time", None),
                ("Last 7 Days", 7),
                ("Last 30 Days", 30),
                ("Last 90 Days", 90)
            ],
            format_func=lambda x: x[0]
        )
    
    with col_filter2:
        aspect_filter = st.selectbox(
            "Aspect Ratio",
            options=["All", "1:1", "4:5", "9:16"]
        )
    
    with col_filter3:
        status_filter = st.selectbox(
            "Status",
            options=["All", "Composed Only", "Base Only"]
        )
    
    # Load assets
    try:
        # Build query based on filters
        query = """
            SELECT a.*, j.prompt, j.created_at as job_created
            FROM assets a
            LEFT JOIN jobs j ON a.job_id = j.id
            WHERE a.org_id = %s
        """
        params = [st.session_state.org_id]
        
        # Date filter
        if date_filter[1]:
            cutoff_date = datetime.now() - timedelta(days=date_filter[1])
            query += " AND a.created_at >= %s"
            params.append(cutoff_date)
        
        # Aspect ratio filter
        if aspect_filter != "All":
            query += " AND a.aspect_ratio = %s"
            params.append(aspect_filter)
        
        # Status filter
        if status_filter == "Composed Only":
            query += " AND a.composed_url IS NOT NULL"
        elif status_filter == "Base Only":
            query += " AND a.composed_url IS NULL"
        
        query += " ORDER BY a.created_at DESC"
        
        assets = db.fetch_all(query, tuple(params))
        
        # Stats
        st.markdown("---")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Total Assets", len(assets))
        
        with stat_col2:
            composed_count = sum(1 for a in assets if a.get("composed_url"))
            st.metric("Composed", composed_count)
        
        with stat_col3:
            base_only_count = sum(1 for a in assets if not a.get("composed_url"))
            st.metric("Base Only", base_only_count)
        
        with stat_col4:
            # Average validation score
            scores = []
            for a in assets:
                if a.get("validation"):
                    try:
                        val_data = a["validation"]
                        # Handle both string and dict
                        if isinstance(val_data, str):
                            val_data = json.loads(val_data)
                        if val_data.get("color_accuracy"):
                            scores.append(val_data["color_accuracy"])
                    except:
                        pass
            
            avg_score = sum(scores) / len(scores) if scores else 0
            st.metric("Avg Quality", f"{avg_score:.1f}%")
        
        # Display assets
        if not assets:
            st.info("📭 No assets found. Generate your first asset to get started!")
            if st.button("🎨 Generate Assets"):
                st.switch_page("pages/2_Generate.py")
            return
        
        st.markdown("---")
        st.subheader(f"📸 Assets ({len(assets)})")
        
        # Display in grid
        for i in range(0, len(assets), 3):
            cols = st.columns(3)
            
            for j, col in enumerate(cols):
                if i + j < len(assets):
                    asset = assets[i + j]
                    
                    with col:
                        # Show composed if available, otherwise base
                        image_url = asset.get("composed_url") or asset["base_url"]
                        st.image(image_url, use_container_width=True)
                        
                        # Asset info
                        st.caption(f"Created: {asset['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        
                        if asset.get("aspect_ratio"):
                            st.caption(f"Format: {asset['aspect_ratio']}")
                        
                        # Validation badge
                        if asset.get("composed_url"):
                            try:
                                val_data = asset["validation"]
                                # Handle both string and dict
                                if isinstance(val_data, str):
                                    val_data = json.loads(val_data)
                                
                                if val_data.get("color_accuracy"):
                                    score = val_data["color_accuracy"]
                                    if score >= 90:
                                        st.success(f"✅ {score:.0f}% Quality")
                                    elif score >= 70:
                                        st.warning(f"⚠️ {score:.0f}% Quality")
                                    else:
                                        st.error(f"❌ {score:.0f}% Quality")
                            except:
                                st.info("ℹ️ Composed")
                        else:
                            st.info("🎨 Base Image")
                        
                        # Action buttons
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("👁️ View", key=f"view_{asset['id']}", use_container_width=True):
                                st.session_state.viewing_asset = asset
                                st.rerun()
                        
                        with col_btn2:
                            if not asset.get("composed_url"):
                                if st.button("✨ Compose", key=f"compose_{asset['id']}", use_container_width=True):
                                    st.session_state.selected_asset_id = str(asset['id'])
                                    st.switch_page("pages/3_Compose_Validate.py")
                            else:
                                # Download button (simulated)
                                st.download_button(
                                    label="📥",
                                    data=image_url,
                                    file_name=f"asset_{asset['id']}.jpg",
                                    mime="image/jpeg",
                                    key=f"download_{asset['id']}",
                                    use_container_width=True
                                )
    
    except Exception as e:
        logger.error(f"Error loading assets: {str(e)}")
        st.error(f"Error loading assets: {str(e)}")
        return
    
    # Asset detail modal
    if "viewing_asset" in st.session_state:
        st.markdown("---")
        st.subheader("🔍 Asset Details")
        
        asset = st.session_state.viewing_asset
        
        col_detail1, col_detail2 = st.columns([2, 1])
        
        with col_detail1:
            image_url = asset.get("composed_url") or asset["base_url"]
            st.image(image_url, use_container_width=True)
        
        with col_detail2:
            st.markdown("### Information")
            st.write(f"**ID**: `{asset['id']}`")
            st.write(f"**Created**: {asset['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Aspect Ratio**: {asset.get('aspect_ratio', 'N/A')}")
            st.write(f"**Type**: {'Composed' if asset.get('composed_url') else 'Base Image'}")
            
            # Prompt if available
            if asset.get("prompt"):
                st.markdown("### 📝 Prompt")
                st.text_area("", asset["prompt"], height=100, disabled=True, label_visibility="collapsed")
            
            # Validation details
            if asset.get("validation"):
                st.markdown("### ✅ Validation")
                try:
                    val_data = asset["validation"]
                    # Handle both string and dict
                    if isinstance(val_data, str):
                        val_data = json.loads(val_data)
                    
                    if val_data.get("logo_verified"):
                        st.success("✅ Logo Verified")
                    
                    if val_data.get("color_accuracy"):
                        st.metric("Color Accuracy", f"{val_data['color_accuracy']:.1f}%")
                    
                    if val_data.get("color_delta_e"):
                        st.metric("Delta E", f"{val_data['color_delta_e']:.2f}")
                    
                    if val_data.get("font_applied"):
                        st.success("✅ Font Applied")
                
                except Exception as e:
                    st.warning("Validation data unavailable")
            
            # Actions
            st.markdown("---")
            
            if st.button("🔙 Back to Library", use_container_width=True):
                del st.session_state.viewing_asset
                st.rerun()
            
            if not asset.get("composed_url"):
                if st.button("✨ Compose This Asset", use_container_width=True):
                    st.session_state.selected_asset_id = str(asset['id'])
                    del st.session_state.viewing_asset
                    st.switch_page("pages/3_Compose_Validate.py")


if __name__ == "__main__":
    main()