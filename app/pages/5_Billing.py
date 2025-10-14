"""
Billing Page
Manage subscription and view usage
"""
import streamlit as st
from datetime import datetime
from app.infra.billing import billing_manager
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Billing", page_icon="💳", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"


def main():
    st.title("💳 Billing & Subscription")
    st.markdown("Manage your plan and view usage")
    
    # Current usage
    st.subheader("📊 Current Usage")
    
    try:
        usage = billing_manager.get_current_usage(st.session_state.org_id)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Monthly Credits",
                usage["monthly_credits"]
            )
        
        with col2:
            st.metric(
                "Credits Used",
                usage["credits_used"],
                delta=f"-{usage['credits_used']}"
            )
        
        with col3:
            st.metric(
                "Credits Remaining",
                usage["credits_remaining"]
            )
        
        with col4:
            usage_pct = (usage["credits_used"] / usage["monthly_credits"]) * 100 if usage["monthly_credits"] > 0 else 0
            st.metric(
                "Usage",
                f"{usage_pct:.1f}%"
            )
        
        # Usage bar
        st.progress(usage_pct / 100)
        
        # Subscription status
        st.markdown("---")
        st.subheader("📋 Subscription Status")
        
        status_col1, status_col2 = st.columns([2, 1])
        
        with status_col1:
            if usage["subscription_status"] == "active":
                st.success("✅ Active Subscription")
            elif usage["subscription_status"] == "trialing":
                st.info("🎉 Trial Period")
            elif usage["subscription_status"] == "past_due":
                st.warning("⚠️ Payment Past Due")
            elif usage["subscription_status"] == "canceled":
                st.error("❌ Subscription Canceled")
            else:
                st.info("ℹ️ No Active Subscription")
            
            st.caption(f"Billing period: {usage['month'].strftime('%B %Y')}")
        
        with status_col2:
            # Manage subscription button
            if usage["subscription_status"] in ["active", "trialing"]:
                if st.button("🔧 Manage Subscription", use_container_width=True):
                    try:
                        portal_session = billing_manager.create_customer_portal_session(
                            org_id=st.session_state.org_id,
                            return_url="http://localhost:8501"
                        )
                        st.markdown(f"[Open Customer Portal]({portal_session['url']})")
                    except Exception as e:
                        st.error("Unable to open customer portal. Please contact support.")
    
    except Exception as e:
        logger.error(f"Error loading usage: {str(e)}")
        st.error("Error loading usage data")
        return
    
    # Available plans
    st.markdown("---")
    st.subheader("💼 Available Plans")
    
    try:
        plans = db.fetch_all("SELECT * FROM plans ORDER BY price_cents ASC")
        
        plan_cols = st.columns(len(plans))
        
        for idx, plan in enumerate(plans):
            with plan_cols[idx]:
                # Plan card
                st.markdown(f"### {plan['name']}")
                st.markdown(f"## ${plan['price_cents'] / 100:.0f}/mo")
                st.markdown(f"**{plan['monthly_credits']} credits/month**")
                
                # Features
                st.markdown("---")
                
                if plan['name'] == 'Starter':
                    st.markdown("""
                    - 30 generations/month
                    - All composition presets
                    - Brand validation
                    - Email support
                    """)
                elif plan['name'] == 'Professional':
                    st.markdown("""
                    - 100 generations/month
                    - All composition presets
                    - Brand validation
                    - Priority support
                    - API access
                    """)
                elif plan['name'] == 'Enterprise':
                    st.markdown("""
                    - 500 generations/month
                    - All composition presets
                    - Brand validation
                    - Dedicated support
                    - API access
                    - Custom integrations
                    """)
                
                st.markdown("---")
                
                # Subscribe button
                if st.button(f"Choose {plan['name']}", key=f"plan_{plan['id']}", use_container_width=True):
                    try:
                        checkout_session = billing_manager.create_checkout_session(
                            org_id=st.session_state.org_id,
                            plan_id=plan['id'],
                            success_url="http://localhost:8501",
                            cancel_url="http://localhost:8501"
                        )
                        st.markdown(f"[Proceed to Checkout]({checkout_session['url']})")
                    except Exception as e:
                        logger.error(f"Error creating checkout: {str(e)}")
                        st.error("Unable to start checkout. Please try again.")
    
    except Exception as e:
        logger.error(f"Error loading plans: {str(e)}")
        st.error("Error loading plans")
        return
    
    # Usage history
    st.markdown("---")
    st.subheader("📈 Usage History")
    
    try:
        usage_history = db.fetch_all(
            """
            SELECT month, credits_used
            FROM usage
            WHERE org_id = %s
            ORDER BY month DESC
            LIMIT 12
            """,
            (st.session_state.org_id,)
        )
        
        if usage_history:
            # Display as table
            st.table({
                "Month": [u["month"].strftime("%B %Y") for u in usage_history],
                "Credits Used": [u["credits_used"] for u in usage_history]
            })
        else:
            st.info("No usage history yet")
    
    except Exception as e:
        logger.error(f"Error loading usage history: {str(e)}")
        st.warning("Unable to load usage history")
    
    # Credit costs
    st.markdown("---")
    st.subheader("💰 Credit Costs")
    
    cost_col1, cost_col2 = st.columns(2)
    
    with cost_col1:
        st.markdown("#### Generation")
        st.write(f"**{billing_manager.credits_per_generation} credits** per image")
        st.caption("Generate AI backgrounds with DALL-E 3")
    
    with cost_col2:
        st.markdown("#### Composition")
        st.write(f"**{billing_manager.credits_per_composition} credits** per composition")
        st.caption("Apply brand overlay and validation")
    
    # Examples
    with st.expander("📊 Credit Usage Examples"):
        st.markdown("""
        **Starter Plan (300 credits/month):**
        - Generate 30 images (30 × 10 credits = 300)
        - OR 20 images + 20 compositions (20 × 10 + 20 × 5 = 300)
        - OR 15 complete workflows (15 × 10 generation + 15 × 5 composition = 225 credits)
        
        **Professional Plan (1000 credits/month):**
        - Generate 100 images
        - OR 66 complete workflows (generation + composition)
        
        **Enterprise Plan (5000 credits/month):**
        - Generate 500 images
        - OR 333 complete workflows
        """)
    
    # FAQ
    st.markdown("---")
    with st.expander("❓ Billing FAQ"):
        st.markdown("""
        **Q: What happens if I run out of credits?**
        A: You can upgrade your plan anytime or wait until your monthly credits reset.
        
        **Q: Do unused credits roll over?**
        A: No, credits reset at the start of each billing period.
        
        **Q: Can I cancel anytime?**
        A: Yes, cancel anytime with no penalties. You'll retain access until the end of your billing period.
        
        **Q: What payment methods do you accept?**
        A: We accept all major credit cards via Stripe.
        
        **Q: Is there a free trial?**
        A: Yes! New accounts start with a 7-day trial of the Starter plan.
        
        **Q: Can I change plans mid-cycle?**
        A: Yes, upgrades take effect immediately. Downgrades take effect at the next billing cycle.
        """)
    
    # Support
    st.markdown("---")
    st.info("💬 Need help? Contact support at support@brandgenerator.com")


if __name__ == "__main__":
    main()