"""Analytics database models.

VARIANTE 3a: Nur aggregierte Zähler, KEINE Suchinhalte!
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from sqlalchemy import Column, Date, Integer, DateTime

# Use same Base as auth models for shared engine
from ..auth.models import Base


class AnalyticsDaily(Base):
    """Daily aggregated analytics metrics.
    
    Speichert NUR Zähler, keine Inhalte (Variante 3a).
    """
    __tablename__ = "analytics_daily"
    
    date = Column(Date, primary_key=True)
    visitors = Column(Integer, nullable=False, default=0)
    mobile = Column(Integer, nullable=False, default=0)
    desktop = Column(Integer, nullable=False, default=0)
    searches = Column(Integer, nullable=False, default=0)
    audio_plays = Column(Integer, nullable=False, default=0)
    errors = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# HINWEIS: Keine AnalyticsQuery Klasse!
# Variante 3a speichert keine Suchinhalte/Query-Texte.
