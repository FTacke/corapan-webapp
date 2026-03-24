"""Template-facing branding source of truth.

This module is the single authority for app identity values rendered through
templates: display names, title formatting, external brand links, contact
details, and static asset filenames used by the shell.
"""

from __future__ import annotations


BRANDING: dict[str, str] = {
    "app_display_name": "CO.RA.PAN",
    "app_short_name": "CORAPAN",
    "app_tagline": "Corpus Radiofonico Panhispanico",
    "page_title_separator": "·",
    "app_meta_description": (
        "CO.RA.PAN is the research web interface for the Corpus Radiofonico "
        "Panhispanico with corpus search, atlas views, and curated metadata access."
    ),
    "institution_name": "Philipps-Universität Marburg",
    "institution_contact_email": "felix.tacke@uni-marburg.de",
    "footer_brand_url": "https://hispanistica.com",
    "footer_brand_label": "Hispanistica at Marburg",
    "footer_brand_badge_alt": "Hispanistica badge",
    "footer_brand_badge_asset": "img/hispanistica_badge.png",
    "project_url": "https://corapan.hispanistica.com",
    "contact_email": "felix.tacke@uni-marburg.de",
    "footer_copyright_holder": "Felix Tacke",
    "app_logo_alt": "CO.RA.PAN logo",
    "favicon_asset": "img/favicon.ico",
    "footer_logo_asset": "img/corapan_basic.png",
    "drawer_logo_light_asset": "img/corapan_lightmode.png",
    "drawer_logo_dark_asset": "img/corapan_darkmode.png",
    "landing_logo_light_asset": "img/corapan_logo_lightmode.png",
    "landing_logo_dark_asset": "img/corapan_logo_darkmode.png",
}


def format_page_title(page_label: str | None = None) -> str:
    """Return a consistently formatted document title."""
    label = (page_label or "").strip()
    if not label:
        return BRANDING["app_display_name"]
    return (
        f"{label} {BRANDING['page_title_separator']} {BRANDING['app_display_name']}"
    )