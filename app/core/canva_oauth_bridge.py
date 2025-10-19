"""
Canva OAuth Bridge
Uses the working backend server for OAuth, stores tokens for Streamlit use
"""
import streamlit as st
import requests
from typing import Optional, Dict, Any
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


class CanvaOAuthBridge:
    """
    Bridge between Streamlit and the working backend OAuth server
    """

    def __init__(self):
        self.backend_url = "http://127.0.0.1:3001"
        self.client_id = settings.CANVA_CLIENT_ID

    def get_authorization_url(self) -> str:
        """
        Get authorization URL from backend server

        Returns:
            Authorization URL to redirect user to
        """
        # The backend server generates the proper OAuth URL
        auth_url = f"{self.backend_url}/authorize"
        logger.info(f"Using backend OAuth URL: {auth_url}")
        return auth_url

    def is_authenticated(self) -> bool:
        """
        Check if user has valid token in backend

        Returns:
            True if authenticated
        """
        try:
            response = requests.get(
                f"{self.backend_url}/isauthorized",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Auth check failed: {str(e)}")
            return False

    def get_access_token(self) -> Optional[str]:
        """
        Get access token from backend

        Returns:
            Access token or None
        """
        try:
            response = requests.get(
                f"{self.backend_url}/token",
                timeout=5
            )

            if response.status_code == 200:
                token = response.text
                logger.info("Retrieved access token from backend")
                return token
            else:
                logger.warning("No token available")
                return None

        except Exception as e:
            logger.error(f"Failed to get token: {str(e)}")
            return None

    def revoke_token(self) -> bool:
        """
        Revoke access token

        Returns:
            True if successful
        """
        try:
            response = requests.get(
                f"{self.backend_url}/revoke",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            return False


# Global bridge instance
canva_oauth_bridge = CanvaOAuthBridge()


def render_canva_auth_button():
    """
    Render Canva authentication button using backend OAuth

    Returns:
        True if user is authenticated
    """
    if not settings.canva_configured:
        st.error("⚠️ Canva integration not configured. Please set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET in .env")
        return False

    if canva_oauth_bridge.is_authenticated():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("✅ Connected to Canva")
        with col2:
            if st.button("Disconnect", key="canva_disconnect"):
                canva_oauth_bridge.revoke_token()
                st.rerun()
        return True
    else:
        st.warning("⚠️ Canva not connected")

        auth_url = canva_oauth_bridge.get_authorization_url()

        st.markdown("""
        ### How to Connect:

        1. Click the button below to authorize Canva
        2. A popup window will open
        3. Log in and click "Authorize"
        4. After you see "Successfully authorized!", click "Check Status" below

        """)

        # JavaScript to open popup window
        popup_js = f"""
        <script>
        function openCanvaAuth() {{
            const width = 600;
            const height = 700;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;

            const popup = window.open(
                '{auth_url}',
                'Canva Authorization',
                `width=${{width}},height=${{height}},left=${{left}},top=${{top}},popup=yes`
            );

            // Check if popup was blocked
            if (!popup || popup.closed || typeof popup.closed == 'undefined') {{
                alert('Popup blocked! Please allow popups for this site and try again.');
            }}
        }}
        </script>
        """

        st.markdown(popup_js, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔗 Connect to Canva", type="primary", key="canva_connect"):
                st.markdown(
                    f'<button onclick="openCanvaAuth()" style="background-color: #4F46E5; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.375rem; cursor: pointer; font-size: 1rem;">Open Authorization Window</button>',
                    unsafe_allow_html=True
                )

        with col2:
            if st.button("🔄 Check Status", key="canva_check"):
                st.rerun()

        # Fallback link
        with st.expander("💡 Popup blocked? Use this link"):
            st.markdown(f"[Open Canva Authorization]({auth_url})")
            st.caption("After authorizing, come back here and click 'Check Status'")

        return False
