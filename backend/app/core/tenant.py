from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, Union
import re

from .database import get_db
from .security import decode_access_token
from ..models import Organization, User
from ..schemas.organization import TenantContext


# Bearer token scheme for authorization
security = HTTPBearer(auto_error=False)


class TenantMiddleware:
    """Middleware to handle multi-tenant isolation"""
    
    def __init__(self):
        self.system_paths = [
            "/docs", "/openapi.json", "/redoc", 
            "/api/health", "/api/system", "/api/licensing"
        ]
        self.public_paths = [
            "/api/auth/login", "/api/auth/register", 
            "/api/public", "/api/org/signup"
        ]

    def extract_tenant_from_request(self, request: Request) -> TenantContext:
        """Extract tenant information from request"""
        
        # Check if this is a system or public path
        path = request.url.path
        if any(path.startswith(sp) for sp in self.system_paths):
            return TenantContext(is_system_admin=True)
        
        if any(path.startswith(pp) for pp in self.public_paths):
            return TenantContext()

        # Extract from custom domain
        host = request.headers.get("host", "").split(":")[0]
        if self._is_custom_domain(host):
            return TenantContext(custom_domain=host)
        
        # Extract from subdomain (e.g., tenant.bcal.com)
        subdomain = self._extract_subdomain(host)
        if subdomain and subdomain != "www":
            return TenantContext(organization_slug=subdomain)
        
        # Extract from path (e.g., /org/tenant-slug/...)
        org_slug = self._extract_org_from_path(path)
        if org_slug:
            return TenantContext(organization_slug=org_slug)
        
        return TenantContext()

    def _is_custom_domain(self, host: str) -> bool:
        """Check if host is a custom domain"""
        # Add your main domain patterns here
        main_domains = ["bcal.com", "localhost", "127.0.0.1"]
        return not any(host.endswith(domain) for domain in main_domains)

    def _extract_subdomain(self, host: str) -> Optional[str]:
        """Extract subdomain from host"""
        if "." in host:
            parts = host.split(".")
            if len(parts) > 2:  # e.g., tenant.bcal.com
                return parts[0]
        return None

    def _extract_org_from_path(self, path: str) -> Optional[str]:
        """Extract organization slug from path"""
        match = re.match(r"/org/([a-z0-9-]+)/", path)
        if match:
            return match.group(1)
        return None


# Dependency to get current tenant context
async def get_tenant_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> TenantContext:
    """Get current tenant context from request and JWT token"""
    
    middleware = TenantMiddleware()
    context = middleware.extract_tenant_from_request(request)
    
    # If we have credentials, decode the token to get user info
    if credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            user_id = payload.get("sub")
            if user_id:
                context.user_id = int(user_id)
                
                # Get user from database to determine role and organization
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    context.user_role = user.role
                    if user.organization_id:
                        context.organization_id = user.organization_id
                    
                    # System admins can access any tenant
                    if user.role == "system_admin":
                        context.is_system_admin = True
        except Exception:
            # Invalid token, but we don't raise error here
            # Let the specific endpoint handle authentication
            pass
    
    # Resolve organization from slug or domain
    if context.organization_slug or context.custom_domain:
        organization = None
        if context.organization_slug:
            organization = db.query(Organization).filter(
                Organization.slug == context.organization_slug,
                Organization.is_active == True
            ).first()
        elif context.custom_domain:
            organization = db.query(Organization).filter(
                Organization.custom_domain == context.custom_domain,
                Organization.is_active == True
            ).first()
        
        if organization:
            context.organization_id = organization.id
        elif not context.is_system_admin:
            raise HTTPException(status_code=404, detail="Organization not found")
    
    return context


# Dependency to require organization context
async def require_organization(
    context: TenantContext = Depends(get_tenant_context)
) -> TenantContext:
    """Require valid organization context"""
    if not context.organization_id and not context.is_system_admin:
        raise HTTPException(
            status_code=400, 
            detail="Organization context required"
        )
    return context


# Dependency to require user authentication
async def require_user(
    context: TenantContext = Depends(get_tenant_context)
) -> TenantContext:
    """Require authenticated user"""
    if not context.user_id:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required"
        )
    return context


# Dependency to require organization member
async def require_org_member(
    context: TenantContext = Depends(require_user),
    db: Session = Depends(get_db)
) -> TenantContext:
    """Require user to be member of the organization"""
    if context.is_system_admin:
        return context
    
    if not context.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Organization context required"
        )
    
    # Check if user belongs to the organization
    user = db.query(User).filter(
        and_(
            User.id == context.user_id,
            User.organization_id == context.organization_id,
            User.is_active == True
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Access denied: not a member of this organization"
        )
    
    return context


# Dependency to require organization admin
async def require_org_admin(
    context: TenantContext = Depends(require_org_member)
) -> TenantContext:
    """Require user to be admin of the organization"""
    if context.is_system_admin:
        return context
    
    if context.user_role not in ["admin", "org_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied: organization admin required"
        )
    
    return context


# Dependency to require system admin
async def require_system_admin(
    context: TenantContext = Depends(require_user)
) -> TenantContext:
    """Require system admin access"""
    if not context.is_system_admin or context.user_role != "system_admin":
        raise HTTPException(
            status_code=403,
            detail="Access denied: system admin required"
        )
    
    return context


# Database query helpers for tenant isolation
class TenantQueryBuilder:
    """Helper class to build tenant-aware database queries"""
    
    @staticmethod
    def filter_by_organization(query, model, organization_id: Optional[int]):
        """Add organization filter to query"""
        if organization_id and hasattr(model, 'organization_id'):
            return query.filter(model.organization_id == organization_id)
        return query
    
    @staticmethod
    def filter_user_by_organization(query, organization_id: Optional[int]):
        """Filter users by organization"""
        if organization_id:
            return query.filter(User.organization_id == organization_id)
        return query


# Utility functions
def get_organization_from_context(
    context: TenantContext,
    db: Session
) -> Optional[Organization]:
    """Get organization object from tenant context"""
    if not context.organization_id:
        return None
    
    return db.query(Organization).filter(
        and_(
            Organization.id == context.organization_id,
            Organization.is_active == True
        )
    ).first()


def enforce_user_limit(
    organization: Organization,
    current_user_count: int,
    additional_users: int = 1
) -> bool:
    """Check if adding users would exceed organization limit"""
    return (current_user_count + additional_users) <= organization.max_users


def get_organization_user_count(
    organization_id: int,
    db: Session
) -> int:
    """Get current active user count for organization"""
    return db.query(User).filter(
        and_(
            User.organization_id == organization_id,
            User.is_active == True
        )
    ).count()
