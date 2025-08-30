"""Add SAAS multi-tenancy support

Revision ID: saas_001
Revises: a797fdadb887
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'saas_001'
down_revision = 'a797fdadb887'
branch_labels = None
depends_on = None


def upgrade():
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=False),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('trial_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_users', sa.Integer(), default=5),
        sa.Column('custom_domain', sa.String(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('favicon_url', sa.String(), nullable=True),
        sa.Column('primary_color', sa.String(), default='#3B82F6'),
        sa.Column('secondary_color', sa.String(), default='#1F2937'),
        sa.Column('accent_color', sa.String(), default='#10B981'),
        sa.Column('brand_name', sa.String(), nullable=True),
        sa.Column('brand_tagline', sa.String(), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('custom_email_from', sa.String(), nullable=True),
        sa.Column('email_signature', sa.Text(), nullable=True),
        sa.Column('features', sa.JSON(), default={}),
        sa.Column('metadata', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)
    op.create_index(op.f('ix_organizations_custom_domain'), 'organizations', ['custom_domain'], unique=True)

    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('stripe_price_id', sa.String(), nullable=True),
        sa.Column('plan_name', sa.String(), default='standard'),
        sa.Column('price_per_user', sa.Numeric(10, 2), default=2.99),
        sa.Column('billing_cycle', sa.String(), default='monthly'),
        sa.Column('currency', sa.String(), default='USD'),
        sa.Column('status', sa.String(), default='active'),
        sa.Column('trial_days', sa.Integer(), default=14),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('licensed_users', sa.Integer(), default=0),
        sa.Column('active_users', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], )
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_organization_id'), 'subscriptions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_stripe_customer_id'), 'subscriptions', ['stripe_customer_id'], unique=True)
    op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=True)

    # Create licenses table
    op.create_table('licenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('license_key', sa.String(), nullable=False),
        sa.Column('license_type', sa.String(), default='standard'),
        sa.Column('max_users', sa.Integer(), default=5),
        sa.Column('max_teams', sa.Integer(), default=10),
        sa.Column('max_bookings_per_month', sa.Integer(), default=1000),
        sa.Column('issued_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('allowed_features', sa.JSON(), default=[]),
        sa.Column('metadata', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], )
    )
    op.create_index(op.f('ix_licenses_id'), 'licenses', ['id'], unique=False)
    op.create_index(op.f('ix_licenses_organization_id'), 'licenses', ['organization_id'], unique=False)
    op.create_index(op.f('ix_licenses_license_key'), 'licenses', ['license_key'], unique=True)

    # Create usage_logs table
    op.create_table('usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('metric_value', sa.Integer(), default=0),
        sa.Column('metric_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], )
    )
    op.create_index(op.f('ix_usage_logs_id'), 'usage_logs', ['id'], unique=False)
    op.create_index(op.f('ix_usage_logs_organization_id'), 'usage_logs', ['organization_id'], unique=False)
    op.create_index(op.f('ix_usage_logs_metric_date'), 'usage_logs', ['metric_date'], unique=False)

    # Modify users table to add organization_id
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    op.create_foreign_key('fk_users_organization_id', 'users', 'organizations', ['organization_id'], ['id'])
    
    # Remove unique constraints from users for multi-tenancy
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Modify teams table to add organization_id
    op.add_column('teams', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_teams_organization_id'), 'teams', ['organization_id'], unique=False)
    op.create_foreign_key('fk_teams_organization_id', 'teams', 'organizations', ['organization_id'], ['id'])
    
    # Remove unique constraint from teams for multi-tenancy
    op.drop_index('ix_teams_name', table_name='teams')
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=False)

    # Create default organization for existing data
    op.execute("""
        INSERT INTO organizations (name, slug, contact_email, is_active, max_users, trial_end_date)
        VALUES ('Default Organization', 'default', 'admin@bcal.com', true, 100, NOW() + INTERVAL '365 days')
    """)
    
    # Update existing users to belong to default organization
    op.execute("""
        UPDATE users SET organization_id = (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1)
        WHERE organization_id IS NULL
    """)
    
    # Update existing teams to belong to default organization
    op.execute("""
        UPDATE teams SET organization_id = (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1)
        WHERE organization_id IS NULL
    """)
    
    # Make organization_id required after data migration
    op.alter_column('users', 'organization_id', nullable=False)
    op.alter_column('teams', 'organization_id', nullable=False)


def downgrade():
    # Remove foreign key constraints and columns
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_teams_organization_id', 'teams', type_='foreignkey')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_teams_organization_id'), table_name='teams')
    op.drop_column('users', 'organization_id')
    op.drop_column('teams', 'organization_id')
    
    # Restore unique constraints
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_teams_name'), table_name='teams')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_teams_name'), 'teams', ['name'], unique=True)
    
    # Drop new tables
    op.drop_table('usage_logs')
    op.drop_table('licenses')
    op.drop_table('subscriptions')
    op.drop_table('organizations')
