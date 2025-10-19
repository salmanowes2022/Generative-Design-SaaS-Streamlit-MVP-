"""
Canva OAuth Callback Handler
Processes OAuth callback and stores token
"""
import streamlit as st
from app.core.canva_oauth import canva_oauth
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Canva Authorization", page_icon="🔗")

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"


def main():
    st.title("🔗 Canva Authorization")

    # Get query parameters
    query_params = st.query_params

    code = query_params.get("code")
    state = query_params.get("state")
    error = query_params.get("error")
    error_description = query_params.get("error_description")

    # Handle error
    if error:
        st.error(f"❌ Authorization failed: {error}")
        if error_description:
            st.error(f"Details: {error_description}")

        st.markdown("---")

        if st.button("🔄 Try Again"):
            st.switch_page("pages/6_Canva_Templates.py")

        return

    # Handle success
    if code and state:
        # Verify state (CSRF protection)
        stored_state = st.session_state.get("canva_oauth_state")

        if stored_state != state:
            st.error("❌ Invalid state parameter. Possible CSRF attack.")
            logger.warning(f"State mismatch: {stored_state} != {state}")
            return

        try:
            with st.spinner("Exchanging authorization code for access token..."):
                # Exchange code for token
                token_data = canva_oauth.exchange_code_for_token(code)

                # Save token to database
                canva_oauth.save_token_to_db(
                    st.session_state.user_id,
                    token_data
                )

                st.success("✅ Successfully connected to Canva!")
                st.balloons()

                st.markdown("---")

                # Show success message
                st.markdown("""
                ### You're all set!

                Your Canva account is now connected. You can:
                - Browse your brand templates
                - Create designs automatically
                - Export designs to high-quality images

                Click below to get started.
                """)

                if st.button("🎨 Go to Templates", type="primary"):
                    st.switch_page("pages/6_Canva_Templates.py")

                if st.button("🚀 Start Generating"):
                    st.switch_page("pages/2_Generate_V2.py")

        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            st.error(f"❌ Failed to complete authorization: {str(e)}")

            st.markdown("---")

            if st.button("🔄 Try Again"):
                st.switch_page("pages/6_Canva_Templates.py")

    else:
        st.info("Waiting for authorization callback...")
        st.markdown("If you were redirected here by mistake, go back to the templates page.")

        if st.button("↩️ Back to Templates"):
            st.switch_page("pages/6_Canva_Templates.py")


if __name__ == "__main__":
    main()
