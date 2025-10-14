"""
Billing Integration
Stripe payment processing and credit management
"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
import stripe
from app.infra.config import settings
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class BillingManager:
    """Manages subscriptions and credit system"""
    
    def __init__(self):
        self.credits_per_generation = settings.CREDITS_PER_GENERATION
        self.credits_per_composition = settings.CREDITS_PER_COMPOSITION
    
    def get_current_usage(self, org_id: UUID) -> Dict[str, Any]:
        """
        Get current month's credit usage for an organization
        
        Args:
            org_id: Organization ID
        
        Returns:
            Usage data with credits used and remaining
        """
        try:
            # Get current month
            current_month = date.today().replace(day=1)
            
            # Get or create usage record
            usage = db.fetch_one(
                "SELECT * FROM usage WHERE org_id = %s AND month = %s",
                (str(org_id), current_month)
            )
            
            if not usage:
                # Create usage record for current month
                usage = db.insert("usage", {
                    "org_id": str(org_id),
                    "month": current_month,
                    "credits_used": 0
                })
            
            # Get subscription to find monthly credits
            subscription = db.fetch_one(
                """
                SELECT s.*, p.monthly_credits
                FROM subscriptions s
                JOIN plans p ON s.plan_id = p.id
                WHERE s.org_id = %s
                """,
                (str(org_id),)
            )
            
            monthly_credits = subscription["monthly_credits"] if subscription else settings.DEFAULT_MONTHLY_CREDITS
            credits_used = usage["credits_used"]
            credits_remaining = max(0, monthly_credits - credits_used)
            
            return {
                "monthly_credits": monthly_credits,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining,
                "month": current_month,
                "subscription_status": subscription["status"] if subscription else "none"
            }
            
        except Exception as e:
            logger.error(f"Error getting usage: {str(e)}")
            raise
    
    def check_credits_available(
        self,
        org_id: UUID,
        credits_needed: int
    ) -> bool:
        """
        Check if organization has enough credits
        
        Args:
            org_id: Organization ID
            credits_needed: Number of credits needed
        
        Returns:
            True if enough credits available
        """
        try:
            usage = self.get_current_usage(org_id)
            return usage["credits_remaining"] >= credits_needed
            
        except Exception as e:
            logger.error(f"Error checking credits: {str(e)}")
            return False
    
    def deduct_credits(
        self,
        org_id: UUID,
        credits: int,
        description: str = ""
    ) -> bool:
        """
        Deduct credits from organization's balance
        
        Args:
            org_id: Organization ID
            credits: Number of credits to deduct
            description: Description of what credits were used for
        
        Returns:
            True if successful
        """
        try:
            # Check if enough credits
            if not self.check_credits_available(org_id, credits):
                logger.warning(f"Insufficient credits for org {org_id}")
                return False
            
            # Get current month
            current_month = date.today().replace(day=1)
            
            # Update usage
            db.execute(
                """
                INSERT INTO usage (org_id, month, credits_used)
                VALUES (%s, %s, %s)
                ON CONFLICT (org_id, month)
                DO UPDATE SET credits_used = usage.credits_used + EXCLUDED.credits_used
                """,
                (str(org_id), current_month, credits)
            )
            
            logger.info(f"Deducted {credits} credits from org {org_id}: {description}")
            return True
            
        except Exception as e:
            logger.error(f"Error deducting credits: {str(e)}")
            raise
    
    def create_checkout_session(
        self,
        org_id: UUID,
        plan_id: UUID,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription
        
        Args:
            org_id: Organization ID
            plan_id: Plan ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
        
        Returns:
            Checkout session data
        """
        try:
            # Get plan details
            plan = db.fetch_one(
                "SELECT * FROM plans WHERE id = %s",
                (str(plan_id),)
            )
            
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': settings.STRIPE_PRICE_ID,  # Use configured price ID
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(org_id),
                metadata={
                    'org_id': str(org_id),
                    'plan_id': str(plan_id)
                }
            )
            
            logger.info(f"Created checkout session for org {org_id}")
            
            return {
                "session_id": session.id,
                "url": session.url
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise
    
    def create_customer_portal_session(
        self,
        org_id: UUID,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer portal session for managing subscription
        
        Args:
            org_id: Organization ID
            return_url: URL to return to after portal
        
        Returns:
            Portal session data
        """
        try:
            # Get subscription
            subscription = db.fetch_one(
                "SELECT * FROM subscriptions WHERE org_id = %s",
                (str(org_id),)
            )
            
            if not subscription or not subscription.get("stripe_subscription_id"):
                raise ValueError("No active subscription found")
            
            # Get Stripe subscription to find customer
            stripe_sub = stripe.Subscription.retrieve(subscription["stripe_subscription_id"])
            customer_id = stripe_sub.customer
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            
            logger.info(f"Created portal session for org {org_id}")
            
            return {
                "url": session.url
            }
            
        except Exception as e:
            logger.error(f"Error creating portal session: {str(e)}")
            raise
    
    def handle_webhook_event(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        
        Args:
            payload: Webhook payload
            sig_header: Stripe signature header
        
        Returns:
            Event handling result
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            event_type = event['type']
            logger.info(f"Handling webhook event: {event_type}")
            
            # Handle different event types
            if event_type == 'checkout.session.completed':
                session = event['data']['object']
                self._handle_checkout_completed(session)
                
            elif event_type == 'customer.subscription.updated':
                subscription = event['data']['object']
                self._handle_subscription_updated(subscription)
                
            elif event_type == 'customer.subscription.deleted':
                subscription = event['data']['object']
                self._handle_subscription_deleted(subscription)
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise
    
    def _handle_checkout_completed(self, session: Dict[str, Any]) -> None:
        """Handle successful checkout"""
        try:
            org_id = session['metadata']['org_id']
            plan_id = session['metadata']['plan_id']
            subscription_id = session['subscription']
            
            # Create or update subscription
            db.execute(
                """
                INSERT INTO subscriptions (org_id, plan_id, stripe_subscription_id, status)
                VALUES (%s, %s, %s, 'active')
                ON CONFLICT (org_id)
                DO UPDATE SET 
                    plan_id = EXCLUDED.plan_id,
                    stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                    status = 'active',
                    updated_at = NOW()
                """,
                (org_id, plan_id, subscription_id)
            )
            
            logger.info(f"Subscription activated for org {org_id}")
            
        except Exception as e:
            logger.error(f"Error handling checkout: {str(e)}")
            raise
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> None:
        """Handle subscription update"""
        try:
            # Update subscription status
            db.execute(
                """
                UPDATE subscriptions
                SET status = %s, current_period_end = to_timestamp(%s), updated_at = NOW()
                WHERE stripe_subscription_id = %s
                """,
                (subscription['status'], subscription['current_period_end'], subscription['id'])
            )
            
            logger.info(f"Subscription updated: {subscription['id']}")
            
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            raise
    
    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> None:
        """Handle subscription cancellation"""
        try:
            db.execute(
                """
                UPDATE subscriptions
                SET status = 'canceled', updated_at = NOW()
                WHERE stripe_subscription_id = %s
                """,
                (subscription['id'],)
            )
            
            logger.info(f"Subscription canceled: {subscription['id']}")
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            raise


# Global billing manager instance
billing_manager = BillingManager()