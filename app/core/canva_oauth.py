"""
Canva OAuth2 Manager for Streamlit
Handles authentication flow and token management
"""
import streamlit as st
import secrets
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.infra.config import settings
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)


class CanvaOAuthManager:
    """
    Manages Canva OAuth2 authentication and token lifecycle
    """

    def __init__(self):
        self.client_id = settings.CANVA_CLIENT_ID
        self.client_secret = settings.CANVA_CLIENT_SECRET
        self.redirect_uri = settings.CANVA_REDIRECT_URI
        self.api_base = settings.CANVA_API_BASE

        # OAuth endpoints
        self.auth_url = "https://www.canva.com/api/oauth/authorize"
        self.token_url = "https://api.canva.com/rest/v1/oauth/token"
        self.revoke_url = "https://api.canva.com/rest/v1/oauth/revoke"

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth2 authorization URL

        Args:
            state: CSRF protection state (generated if not provided)

        Returns:
            Authorization URL to redirect user to
        """
        if not self.client_id:
            raise ValueError("CANVA_CLIENT_ID not configured")

        # Generate state for CSRF protection
        if not state:
            state = secrets.token_urlsafe(32)
            st.session_state.canva_oauth_state = state

        # Scopes needed for design creation
        scopes = [
            "asset:read",
            "design:content:read",
            "design:content:write",
            "design:meta:read",
            "profile:read"
        ]
        scope_string = " ".join(scopes)

        auth_url = (
            f"{self.auth_url}"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scope_string}"
            f"&state={state}"
        )

        logger.info("Generated Canva authorization URL")
        return auth_url

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from callback

        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "expires_in": int,
                "token_type": str,
                "scope": str
            }
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Canva credentials not configured")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }

        try:
            response = requests.post(
                self.token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            logger.info("Successfully exchanged code for Canva access token")

            return token_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise ValueError(f"Failed to get Canva access token: {str(e)}")

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token from previous auth

        Returns:
            New token data
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Canva credentials not configured")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(
                self.token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            logger.info("Successfully refreshed Canva access token")

            return token_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise ValueError(f"Failed to refresh Canva access token: {str(e)}")

    def revoke_token(self, token: str) -> bool:
        """
        Revoke access or refresh token

        Args:
            token: Token to revoke

        Returns:
            True if successful
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Canva credentials not configured")

        payload = {
            "token": token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(
                self.revoke_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()

            logger.info("Successfully revoked Canva token")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Token revoke error: {str(e)}")
            return False

    def save_token_to_db(self, user_id: str, token_data: Dict[str, Any]):
        """
        Save token data to database

        Args:
            user_id: User identifier
            token_data: Token data from OAuth flow
        """
        try:
            expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))

            db.execute(
                """
                INSERT INTO canva_tokens (user_id, access_token, refresh_token, expires_at, scope, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (user_id)
                DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    scope = EXCLUDED.scope,
                    updated_at = NOW()
                """,
                (
                    user_id,
                    token_data["access_token"],
                    token_data.get("refresh_token"),
                    expires_at,
                    token_data.get("scope", "")
                )
            )

            logger.info(f"Saved Canva token for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to save token to database: {str(e)}")
            raise

    def get_token_from_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve token data from database

        Args:
            user_id: User identifier

        Returns:
            Token data or None if not found
        """
        try:
            result = db.fetchone(
                """
                SELECT access_token, refresh_token, expires_at, scope
                FROM canva_tokens
                WHERE user_id = %s
                """,
                (user_id,)
            )

            if not result:
                return None

            token_data = {
                "access_token": result[0],
                "refresh_token": result[1],
                "expires_at": result[2],
                "scope": result[3]
            }

            # Check if token is expired
            if token_data["expires_at"] < datetime.now():
                logger.info("Token expired, refreshing...")
                # Refresh token
                new_token_data = self.refresh_token(token_data["refresh_token"])
                self.save_token_to_db(user_id, new_token_data)
                return new_token_data

            return token_data

        except Exception as e:
            logger.error(f"Failed to get token from database: {str(e)}")
            return None

    def is_authenticated(self, user_id: str) -> bool:
        """
        Check if user has valid Canva authentication

        Args:
            user_id: User identifier

        Returns:
            True if authenticated
        """
        token_data = self.get_token_from_db(user_id)
        return token_data is not None

    def get_access_token(self, user_id: str) -> Optional[str]:
        """
        Get valid access token for user

        Args:
            user_id: User identifier

        Returns:
            Access token or None
        """
        token_data = self.get_token_from_db(user_id)
        if token_data:
            return token_data["access_token"]
        return None

    def disconnect(self, user_id: str) -> bool:
        """
        Disconnect Canva integration for user

        Args:
            user_id: User identifier

        Returns:
            True if successful
        """
        try:
            # Get token to revoke
            token_data = self.get_token_from_db(user_id)
            if token_data:
                self.revoke_token(token_data["access_token"])

            # Delete from database
            db.execute(
                "DELETE FROM canva_tokens WHERE user_id = %s",
                (user_id,)
            )

            logger.info(f"Disconnected Canva for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to disconnect Canva: {str(e)}")
            return False


# Global OAuth manager instance
canva_oauth = CanvaOAuthManager()


# Streamlit UI helpers

def render_canva_auth_button():
    """
    Render Canva authentication button in Streamlit

    Returns:
        True if user clicked connect button
    """
    if not settings.canva_configured:
        st.error("⚠️ Canva integration not configured. Please set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET in .env")
        return False

    user_id = st.session_state.get("user_id", "default_user")

    if canva_oauth.is_authenticated(user_id):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("✅ Connected to Canva")
        with col2:
            if st.button("Disconnect", key="canva_disconnect"):
                canva_oauth.disconnect(user_id)
                st.rerun()
        return True
    else:
        st.warning("⚠️ Canva not connected")
        if st.button("🔗 Connect to Canva", type="primary", key="canva_connect"):
            auth_url = canva_auth.get_authorization_url()
            st.markdown(f"[Click here to authorize Canva]({auth_url})")
            st.info("👆 After authorizing, you'll be redirected back to the app")
        return False
