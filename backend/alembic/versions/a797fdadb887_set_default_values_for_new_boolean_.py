"""Set default values for new boolean fields

Revision ID: a797fdadb887
Revises: c4940ed0d973
Create Date: 2025-08-15 08:41:41.418726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a797fdadb887'
down_revision = 'c4940ed0d973'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set default values for new boolean fields in availabilities table
    op.execute("""
        UPDATE availabilities 
        SET is_recurring = false,
            sync_with_calendar = false,
            buffer_before_minutes = 0,
            buffer_after_minutes = 0,
            min_notice_hours = 2,
            max_booking_days = 90,
            slot_duration_minutes = 30,
            meeting_type = 'general'
        WHERE is_recurring IS NULL
    """)
    
    # Set default values for new fields in users table
    op.execute("""
        UPDATE users 
        SET auth_provider = 'local',
            email_notifications = true,
            sms_notifications = false,
            reminder_preferences = '24h,1h'
        WHERE auth_provider IS NULL
    """)


def downgrade() -> None:
    # No downgrade needed for data updates
    pass
