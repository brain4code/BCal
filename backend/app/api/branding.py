from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
import uuid
import shutil
from pathlib import Path

from ..core.database import get_db
from ..core.tenant import get_tenant_context, require_org_admin, TenantContext
from ..models import Organization
from ..schemas.organization import OrganizationUpdate

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads/branding")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("/branding")
async def get_branding_config(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_tenant_context)
):
    """Get branding configuration for current organization or default"""
    
    if context.organization_id:
        organization = db.query(Organization).filter(
            Organization.id == context.organization_id
        ).first()
        
        if organization:
            return {
                "brand_name": organization.brand_name or "BCal",
                "brand_tagline": organization.brand_tagline,
                "logo_url": organization.logo_url,
                "favicon_url": organization.favicon_url,
                "primary_color": organization.primary_color,
                "secondary_color": organization.secondary_color,
                "accent_color": organization.accent_color,
                "custom_css": organization.custom_css,
                "custom_domain": organization.custom_domain,
                "features": organization.features
            }
    
    # Return default branding
    return {
        "brand_name": "BCal",
        "brand_tagline": "Schedule meetings effortlessly",
        "logo_url": None,
        "favicon_url": None,
        "primary_color": "#3B82F6",
        "secondary_color": "#1F2937",
        "accent_color": "#10B981",
        "custom_css": None,
        "custom_domain": None,
        "features": {
            "teams": True,
            "calendar_integration": True,
            "email_notifications": True,
            "sms_notifications": False,
            "video_conferencing": True,
            "custom_branding": False,
            "api_access": False,
            "advanced_analytics": False
        }
    }


@router.put("/branding")
async def update_branding(
    branding_data: Dict[str, Any],
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Update branding configuration"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Validate color formats
    color_fields = ["primary_color", "secondary_color", "accent_color"]
    for field in color_fields:
        if field in branding_data:
            color = branding_data[field]
            if color and not _is_valid_hex_color(color):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid color format for {field}. Use #RRGGBB format."
                )
    
    # Update allowed fields
    allowed_fields = [
        "brand_name", "brand_tagline", "primary_color", 
        "secondary_color", "accent_color", "custom_css"
    ]
    
    for field in allowed_fields:
        if field in branding_data:
            setattr(organization, field, branding_data[field])
    
    db.commit()
    db.refresh(organization)
    
    return {
        "status": "success",
        "message": "Branding updated successfully"
    }


@router.post("/branding/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Upload organization logo"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Validate file
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPEG, PNG, GIF, WebP, SVG"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5MB"
        )
    
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        filename = f"logo_{organization.id}_{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update organization
        logo_url = f"/uploads/branding/{filename}"
        organization.logo_url = logo_url
        db.commit()
        
        return {
            "status": "success",
            "logo_url": logo_url,
            "message": "Logo uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload logo: {str(e)}"
        )


@router.post("/branding/favicon")
async def upload_favicon(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Upload organization favicon"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Validate file (favicon should be ICO, PNG, or SVG)
    favicon_types = {"image/x-icon", "image/png", "image/svg+xml"}
    if file.content_type not in favicon_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: ICO, PNG, SVG"
        )
    
    # Check file size (smaller limit for favicon)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 1024 * 1024:  # 1MB
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 1MB"
        )
    
    try:
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        filename = f"favicon_{organization.id}_{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update organization
        favicon_url = f"/uploads/branding/{filename}"
        organization.favicon_url = favicon_url
        db.commit()
        
        return {
            "status": "success",
            "favicon_url": favicon_url,
            "message": "Favicon uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload favicon: {str(e)}"
        )


@router.delete("/branding/logo")
async def remove_logo(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Remove organization logo"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Remove file if exists
    if organization.logo_url:
        try:
            filename = organization.logo_url.split("/")[-1]
            file_path = UPLOAD_DIR / filename
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # Ignore file deletion errors
    
    # Update organization
    organization.logo_url = None
    db.commit()
    
    return {
        "status": "success",
        "message": "Logo removed successfully"
    }


@router.delete("/branding/favicon")
async def remove_favicon(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Remove organization favicon"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Remove file if exists
    if organization.favicon_url:
        try:
            filename = organization.favicon_url.split("/")[-1]
            file_path = UPLOAD_DIR / filename
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # Ignore file deletion errors
    
    # Update organization
    organization.favicon_url = None
    db.commit()
    
    return {
        "status": "success", 
        "message": "Favicon removed successfully"
    }


@router.get("/branding/themes")
async def get_available_themes():
    """Get available color themes"""
    
    themes = {
        "default": {
            "name": "Default Blue",
            "primary_color": "#3B82F6",
            "secondary_color": "#1F2937",
            "accent_color": "#10B981"
        },
        "professional": {
            "name": "Professional",
            "primary_color": "#1F2937",
            "secondary_color": "#374151",
            "accent_color": "#3B82F6"
        },
        "vibrant": {
            "name": "Vibrant",
            "primary_color": "#7C3AED",
            "secondary_color": "#1F2937",
            "accent_color": "#F59E0B"
        },
        "nature": {
            "name": "Nature",
            "primary_color": "#059669",
            "secondary_color": "#1F2937",
            "accent_color": "#34D399"
        },
        "sunset": {
            "name": "Sunset",
            "primary_color": "#DC2626",
            "secondary_color": "#1F2937",
            "accent_color": "#F97316"
        },
        "ocean": {
            "name": "Ocean",
            "primary_color": "#0891B2",
            "secondary_color": "#1E40AF",
            "accent_color": "#06B6D4"
        }
    }
    
    return themes


@router.post("/branding/themes/{theme_name}")
async def apply_theme(
    theme_name: str,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_org_admin)
):
    """Apply a predefined theme"""
    
    organization = db.query(Organization).filter(
        Organization.id == context.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get theme configuration
    themes_response = await get_available_themes()
    themes = themes_response if isinstance(themes_response, dict) else {}
    
    if theme_name not in themes:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    theme = themes[theme_name]
    
    # Apply theme colors
    organization.primary_color = theme["primary_color"]
    organization.secondary_color = theme["secondary_color"]
    organization.accent_color = theme["accent_color"]
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Applied {theme['name']} theme successfully",
        "theme": theme
    }


@router.get("/branding/preview")
async def get_branding_preview(
    primary_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
    accent_color: Optional[str] = None,
    context: TenantContext = Depends(get_tenant_context)
):
    """Preview branding with custom colors"""
    
    # Use provided colors or defaults
    colors = {
        "primary_color": primary_color or "#3B82F6",
        "secondary_color": secondary_color or "#1F2937", 
        "accent_color": accent_color or "#10B981"
    }
    
    # Validate colors
    for field, color in colors.items():
        if not _is_valid_hex_color(color):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid color format for {field}. Use #RRGGBB format."
            )
    
    # Generate CSS variables
    css_variables = f"""
    :root {{
        --primary-color: {colors['primary_color']};
        --secondary-color: {colors['secondary_color']};
        --accent-color: {colors['accent_color']};
        --primary-rgb: {_hex_to_rgb(colors['primary_color'])};
        --secondary-rgb: {_hex_to_rgb(colors['secondary_color'])};
        --accent-rgb: {_hex_to_rgb(colors['accent_color'])};
    }}
    """
    
    return {
        "colors": colors,
        "css_variables": css_variables.strip(),
        "preview_html": _generate_preview_html(colors)
    }


# Helper functions
def _is_valid_hex_color(color: str) -> bool:
    """Validate hex color format"""
    import re
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex color to RGB values"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


def _generate_preview_html(colors: Dict[str, str]) -> str:
    """Generate preview HTML with custom colors"""
    return f"""
    <div style="background: {colors['secondary_color']}; padding: 20px; border-radius: 8px;">
        <div style="background: white; padding: 20px; border-radius: 6px; margin-bottom: 15px;">
            <h3 style="color: {colors['primary_color']}; margin: 0 0 10px 0;">BCal Preview</h3>
            <p style="color: {colors['secondary_color']}; margin: 0 0 15px 0;">
                This is how your booking page will look with these colors.
            </p>
            <button style="
                background: {colors['primary_color']}; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 4px; 
                margin-right: 10px;
            ">Book Meeting</button>
            <button style="
                background: {colors['accent_color']}; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 4px;
            ">View Calendar</button>
        </div>
    </div>
    """
