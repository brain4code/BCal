import stripe
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..core.config import settings
from ..models import Organization, Subscription, User, License
from ..schemas.organization import SubscriptionCreate, SubscriptionUpdate
from .licensing import LicensingService

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class BillingService:
    """Service for handling Stripe billing operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.licensing_service = LicensingService(db)
    
    async def create_customer(self, organization: Organization) -> str:
        """Create a Stripe customer for the organization"""
        try:
            customer = stripe.Customer.create(
                email=organization.contact_email,
                name=organization.name,
                description=f"BCal Organization: {organization.name}",
                metadata={
                    "organization_id": organization.id,
                    "organization_slug": organization.slug
                }
            )
            
            logger.info(f"Created Stripe customer {customer.id} for organization {organization.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise Exception(f"Billing service error: {str(e)}")
    
    async def create_subscription(
        self,
        organization: Organization,
        user_count: int,
        payment_method_id: str,
        trial_days: int = 14
    ) -> Subscription:
        """Create a new subscription with Stripe"""
        
        # Check if organization already has an active subscription
        existing_subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.organization_id == organization.id,
                Subscription.status.in_(["active", "trialing"])
            )
        ).first()
        
        if existing_subscription:
            raise Exception("Organization already has an active subscription")
        
        try:
            # Create or get Stripe customer
            stripe_customer_id = await self._get_or_create_customer(organization)
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer_id,
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                stripe_customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            # Create Stripe price for $2.99 per user per month
            price = stripe.Price.create(
                unit_amount=299,  # $2.99 in cents
                currency='usd',
                recurring={'interval': 'month'},
                product_data={
                    'name': 'BCal Standard Plan',
                    'description': 'Calendar booking platform - per user per month'
                },
                metadata={
                    'organization_id': organization.id,
                    'plan_type': 'standard'
                }
            )
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{
                    'price': price.id,
                    'quantity': user_count,
                }],
                trial_period_days=trial_days,
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'organization_id': organization.id,
                    'organization_name': organization.name
                }
            )
            
            # Create local subscription record
            subscription = Subscription(
                organization_id=organization.id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription.id,
                stripe_price_id=price.id,
                plan_name="standard",
                price_per_user=2.99,
                billing_cycle="monthly",
                currency="USD",
                status="trialing" if trial_days > 0 else "active",
                trial_days=trial_days,
                licensed_users=user_count,
                active_users=user_count,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                next_billing_date=datetime.fromtimestamp(stripe_subscription.current_period_end)
            )
            
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)
            
            # Create license
            await self.licensing_service.create_license(
                organization.id,
                max_users=user_count,
                license_type="standard"
            )
            
            logger.info(f"Created subscription {subscription.id} for organization {organization.id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            self.db.rollback()
            raise Exception(f"Billing service error: {str(e)}")
    
    async def update_subscription_quantity(
        self,
        subscription: Subscription,
        new_user_count: int
    ) -> Subscription:
        """Update subscription quantity (user count)"""
        
        try:
            # Get Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Update quantity
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0]['id'],
                    'quantity': new_user_count,
                }],
                proration_behavior='always_invoice'
            )
            
            # Update local record
            subscription.licensed_users = new_user_count
            subscription.active_users = new_user_count
            self.db.commit()
            
            # Update license
            await self.licensing_service.update_license_limits(
                subscription.organization_id,
                max_users=new_user_count
            )
            
            logger.info(f"Updated subscription {subscription.id} to {new_user_count} users")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            self.db.rollback()
            raise Exception(f"Billing service error: {str(e)}")
    
    async def cancel_subscription(self, subscription: Subscription) -> Subscription:
        """Cancel a subscription"""
        
        try:
            # Cancel Stripe subscription at period end
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update local record
            subscription.status = "cancelled"
            self.db.commit()
            
            # Deactivate license
            await self.licensing_service.deactivate_license(subscription.organization_id)
            
            logger.info(f"Cancelled subscription {subscription.id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            self.db.rollback()
            raise Exception(f"Billing service error: {str(e)}")
    
    async def handle_webhook(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Handle Stripe webhook events"""
        
        try:
            if event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(event_data)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event_data)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook {event_type}: {str(e)}")
            return False
    
    async def get_billing_portal_url(self, organization: Organization) -> str:
        """Generate Stripe billing portal URL"""
        
        subscription = self.db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).first()
        
        if not subscription or not subscription.stripe_customer_id:
            raise Exception("No billing information found")
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=f"https://{organization.slug}.bcal.com/dashboard/billing"
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session: {str(e)}")
            raise Exception(f"Billing service error: {str(e)}")
    
    async def get_usage_based_invoice_preview(
        self,
        organization: Organization,
        user_count: int
    ) -> Dict[str, Any]:
        """Get preview of next invoice based on usage"""
        
        subscription = self.db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).first()
        
        if not subscription:
            raise Exception("No subscription found")
        
        try:
            # Get upcoming invoice
            upcoming_invoice = stripe.Invoice.upcoming(
                customer=subscription.stripe_customer_id,
                subscription=subscription.stripe_subscription_id,
                subscription_items=[{
                    'id': subscription.stripe_subscription_id,
                    'quantity': user_count
                }]
            )
            
            return {
                "amount_due": upcoming_invoice.amount_due / 100,  # Convert from cents
                "currency": upcoming_invoice.currency,
                "period_start": datetime.fromtimestamp(upcoming_invoice.period_start),
                "period_end": datetime.fromtimestamp(upcoming_invoice.period_end),
                "user_count": user_count,
                "per_user_cost": 2.99,
                "total_cost": user_count * 2.99
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get invoice preview: {str(e)}")
            raise Exception(f"Billing service error: {str(e)}")
    
    # Private methods
    async def _get_or_create_customer(self, organization: Organization) -> str:
        """Get existing or create new Stripe customer"""
        
        # Check if organization already has a subscription with customer ID
        existing_subscription = self.db.query(Subscription).filter(
            Subscription.organization_id == organization.id
        ).first()
        
        if existing_subscription and existing_subscription.stripe_customer_id:
            return existing_subscription.stripe_customer_id
        
        return await self.create_customer(organization)
    
    async def _handle_payment_succeeded(self, event_data: Dict[str, Any]):
        """Handle successful payment webhook"""
        
        invoice = event_data["object"]
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if subscription:
                subscription.status = "active"
                self.db.commit()
                
                # Ensure license is active
                await self.licensing_service.activate_license(subscription.organization_id)
                
                logger.info(f"Payment succeeded for subscription {subscription.id}")
    
    async def _handle_payment_failed(self, event_data: Dict[str, Any]):
        """Handle failed payment webhook"""
        
        invoice = event_data["object"]
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if subscription:
                subscription.status = "past_due"
                self.db.commit()
                
                # TODO: Send payment failed notification email
                
                logger.warning(f"Payment failed for subscription {subscription.id}")
    
    async def _handle_subscription_updated(self, event_data: Dict[str, Any]):
        """Handle subscription updated webhook"""
        
        stripe_subscription = event_data["object"]
        subscription_id = stripe_subscription["id"]
        
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            # Update subscription details
            subscription.status = stripe_subscription["status"]
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription["current_period_start"]
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription["current_period_end"]
            )
            
            # Update user count if changed
            if stripe_subscription["items"]["data"]:
                new_quantity = stripe_subscription["items"]["data"][0]["quantity"]
                subscription.licensed_users = new_quantity
                subscription.active_users = new_quantity
            
            self.db.commit()
            
            logger.info(f"Updated subscription {subscription.id} from webhook")
    
    async def _handle_subscription_deleted(self, event_data: Dict[str, Any]):
        """Handle subscription deleted webhook"""
        
        stripe_subscription = event_data["object"]
        subscription_id = stripe_subscription["id"]
        
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "cancelled"
            self.db.commit()
            
            # Deactivate license
            await self.licensing_service.deactivate_license(subscription.organization_id)
            
            logger.info(f"Subscription {subscription.id} deleted via webhook")
    
    def get_subscription_by_organization(self, organization_id: int) -> Optional[Subscription]:
        """Get active subscription for organization"""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.organization_id == organization_id,
                Subscription.status.in_(["active", "trialing", "past_due"])
            )
        ).first()
    
    def calculate_monthly_cost(self, user_count: int) -> float:
        """Calculate monthly cost for given user count"""
        return user_count * 2.99
