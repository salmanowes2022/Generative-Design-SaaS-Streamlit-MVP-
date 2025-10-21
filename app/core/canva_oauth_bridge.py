"""
Canva OAuth Bridge
Uses the working backend server for OAuth, stores tokens for Streamlit use
"""
import streamlit as st
import requests
import json
import os
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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
        # Path to the backend database where tokens are stored
        self.db_path = Path(__file__).parent.parent.parent / "canva-connect-api-starter-kit" / "demos" / "playground" / "backend" / "db.json"
        # Path to .env file for encryption key
        self.env_path = Path(__file__).parent.parent.parent / "canva-connect-api-starter-kit" / "demos" / "playground" / ".env"

    def _get_encryption_key(self) -> Optional[bytes]:
        """Get the DATABASE_ENCRYPTION_KEY from .env file"""
        try:
            if self.env_path.exists():
                with open(self.env_path, 'r') as f:
                    for line in f:
                        if line.startswith('DATABASE_ENCRYPTION_KEY='):
                            key_b64 = line.split('=', 1)[1].strip()
                            return base64.b64decode(key_b64)
            logger.error("Could not find DATABASE_ENCRYPTION_KEY in .env file")
            return None
        except Exception as e:
            logger.error(f"Failed to get encryption key: {str(e)}")
            return None

    def _decrypt_token(self, encrypted_data: Dict[str, str]) -> Optional[str]:
        """Decrypt token using AES-GCM (same as backend)"""
        try:
            key = self._get_encryption_key()
            if not key:
                return None

            iv = base64.b64decode(encrypted_data['iv'])
            ciphertext = base64.b64decode(encrypted_data['encryptedData'])

            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(iv, ciphertext, None)

            # Parse the decrypted JSON to get access_token
            token_data = json.loads(decrypted.decode('utf-8'))
            return token_data.get('access_token')
        except Exception as e:
            logger.error(f"Failed to decrypt token: {str(e)}")
            return None

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
        Check if user has valid token in backend or database file

        Returns:
            True if authenticated
        """
        # First try HTTP endpoint
        try:
            response = requests.get(
                f"{self.backend_url}/isauthorized",
                timeout=2
            )
            if response.status_code == 200:
                logger.info("User is authenticated (via HTTP)")
                return True
        except Exception as e:
            logger.warning(f"HTTP auth check failed: {str(e)}, checking database file...")

        # Fallback: Check database file directly
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    db_data = json.load(f)
                    users = db_data.get('users', [])
                    if users and len(users) > 0:
                        # Check if any user has a token
                        has_token = any(user.get('token') for user in users)
                        if has_token:
                            logger.info(f"User is authenticated (found {len(users)} user(s) with tokens in db.json)")
                            return True
        except Exception as e:
            logger.error(f"Database file check failed: {str(e)}")

        logger.info("User is not authenticated")
        return False

    def get_access_token(self) -> Optional[str]:
        """
        Get access token from backend or database file

        Returns:
            Access token or None
        """
        # First try HTTP endpoint
        try:
            response = requests.get(
                f"{self.backend_url}/token",
                timeout=2
            )

            if response.status_code == 200:
                token = response.text
                logger.info("Retrieved access token from backend (via HTTP)")
                return token
        except Exception as e:
            logger.warning(f"HTTP token fetch failed: {str(e)}, checking database file...")

        # Fallback: Read and decrypt token from database file
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    db_data = json.load(f)
                    users = db_data.get('users', [])

                    if users and len(users) > 0:
                        # Get the first user's token (in production, match by user ID)
                        user = users[0]
                        encrypted_token = user.get('token')

                        if encrypted_token:
                            access_token = self._decrypt_token(encrypted_token)
                            if access_token:
                                logger.info("Retrieved and decrypted access token from db.json")
                                return access_token
                            else:
                                logger.error("Failed to decrypt token")
                        else:
                            logger.error("No token found in user data")
        except Exception as e:
            logger.error(f"Database file token fetch failed: {str(e)}")

        logger.error("Failed to get access token from any source")
        return None

    def list_brand_templates(self) -> Optional[Dict[str, Any]]:
        """
        List brand templates from Canva

        Returns:
            Dict with template info or None if failed
            {
                "items": [
                    {
                        "id": "template_id",
                        "name": "Template Name",
                        "thumbnail": {"url": "..."}
                    }
                ],
                "continuation": "..."
            }
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                logger.error("No access token available for brand templates list")
                return None

            api_base = settings.CANVA_API_BASE
            url = f"{api_base}/brand-templates"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Retrieved {len(data.get('items', []))} brand templates from Canva")
            return data

        except Exception as e:
            logger.error(f"Failed to list brand templates: {str(e)}")
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
