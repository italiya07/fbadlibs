import logging
import stripe
from adsapi.models import User
from decouple import config
from django.conf import settings

MONTH = 'm'
ANNUAL = 'a'

API_KEY = config('STRIPE_SECRET_KEY')
logger = logging.getLogger(__name__)


class VideosMonthPlan:
    def __init__(self):
        self.stripe_plan_id = config('STRIPE_PLAN_MONTHLY_ID')
        self.amount = 1000


class VideosAnnualPlan:
    def __init__(self):
        self.stripe_plan_id = config('STRIPE_PLAN_ANNUAL_ID')
        self.amount = 10000


class VideosPlan:
    def __init__(self, plan_id):
        """
        plan_id is either string 'm' (stands for monthly)
        or a string letter 'a' (which stands for annual)
        """
        if plan_id == MONTH:
            self.plan = VideosMonthPlan()
            self.id = MONTH
        elif plan_id == ANNUAL:
            self.plan = VideosAnnualPlan()
            self.id = ANNUAL
        else:
            raise ValueError('Invalid plan_id value')

        self.currency = 'usd'

    @property
    def stripe_plan_id(self):
        return self.plan.stripe_plan_id

    @property
    def amount(self):
        return self.plan.amount

def set_paid_until(charge):
    stripe.api_key = API_KEY
    email = charge.customer_email
    current_period_end = charge.lines.data[0].period["end"]
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        logger.warning(
            f"User with email {email} not found"
        )
        return False

    user.set_paid_until(current_period_end)
    logger.info(
        f"Profile with {current_period_end} saved for user {email}"
    )