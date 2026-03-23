#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_metadata.py - FAIR/DFG-compliant Metadata Export for CO.RA.PAN

Generates standardized metadata files from transcript JSONs:
  - corapan_recordings.tsv  (Tab-separated)
  - corapan_recordings.json (JSON array)
  - corapan_recordings.jsonld (JSON-LD with schema.org context)
  - corapan_corpus_metadata.json (Corpus-level metadata)
  - corapan_corpus_metadata.jsonld (Corpus-level JSON-LD)
  - tei/ subfolder with TEI header files per recording
  - tei_headers.zip (optional ZIP archive)

Output is written to runtime/data/public/metadata/vYYYY-MM-DD/ with a "latest" symlink.

Usage:
    python export_metadata.py --corpus-version v1.0 --release-date 2025-12-15
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from xml.dom import minidom

# ==============================================================================
# PATH CONFIGURATION - Same pattern as database_creation_v3.py
# ==============================================================================

# Find project root relative to script location
# Path: LOKAL/metadata/export_metadata.py
SCRIPT_DIR = Path(__file__).resolve().parent  # LOKAL/metadata/
PROJECT_ROOT = SCRIPT_DIR.parent.parent        # CO.RA.PAN-WEB/
TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts"

def resolve_runtime_root() -> Path:
    runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")
    if not runtime_root:
        raise RuntimeError(
            "CORAPAN_RUNTIME_ROOT not configured. "
            "Runtime data is required for metadata export."
        )
    return Path(runtime_root)

RUNTIME_ROOT = resolve_runtime_root()
DATA_ROOT = RUNTIME_ROOT / "data"
PUBLIC_ROOT = DATA_ROOT / "public"
PUBLIC_METADATA_DIR = PUBLIC_ROOT / "metadata"
PUBLIC_METADATA_DIR.mkdir(parents=True, exist_ok=True)

# Import country code configuration (same pattern as database_creation_v3.py)
import importlib.util
COUNTRIES_PY = PROJECT_ROOT / "src" / "app" / "config" / "countries.py"

if COUNTRIES_PY.exists():
    spec = importlib.util.spec_from_file_location("countries_module", COUNTRIES_PY)
    countries_module = importlib.util.module_from_spec(spec)
    sys.modules['countries_module'] = countries_module
    spec.loader.exec_module(countries_module)
    get_location = countries_module.get_location
    normalize_country_code = countries_module.normalize_country_code
else:
    # Fallback if countries.py not available
    def get_location(code: str):
        return None
    def normalize_country_code(code: str) -> str:
        return code.upper() if code else ""

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ==============================================================================
# COUNTRY CODE MAPPINGS (ISO 3166-1 alpha-3 to alpha-2 and full names)
# ==============================================================================

# Map alpha-3 to alpha-2 codes
ALPHA3_TO_ALPHA2: dict[str, str] = {
    "ARG": "AR",
    "BOL": "BO",
    "CHL": "CL",
    "COL": "CO",
    "CRI": "CR",
    "CUB": "CU",
    "DOM": "DO",
    "ECU": "EC",
    "ESP": "ES",
    "GTM": "GT",
    "HND": "HN",
    "MEX": "MX",
    "NIC": "NI",
    "PAN": "PA",
    "PER": "PE",
    "PRY": "PY",
    "SLV": "SV",
    "URY": "UY",
    "USA": "US",
    "VEN": "VE",
}

# Map alpha-3 to full country names in Spanish
ALPHA3_TO_NAME: dict[str, str] = {
    "ARG": "Argentina",
    "ARG-CBA": "Argentina (Córdoba)",
    "ARG-CHU": "Argentina (Chubut)",
    "ARG-SDE": "Argentina (Santiago del Estero)",
    "BOL": "Bolivia",
    "CHL": "Chile",
    "COL": "Colombia",
    "CRI": "Costa Rica",
    "CUB": "Cuba",
    "DOM": "República Dominicana",
    "ECU": "Ecuador",
    "ESP": "España",
    "ESP-CAN": "España (Canarias)",
    "ESP-SEV": "España (Sevilla)",
    "GTM": "Guatemala",
    "HND": "Honduras",
    "MEX": "México",
    "NIC": "Nicaragua",
    "PAN": "Panamá",
    "PER": "Perú",
    "PRY": "Paraguay",
    "SLV": "El Salvador",
    "URY": "Uruguay",
    "USA": "Estados Unidos",
    "VEN": "Venezuela",
}

# ==============================================================================
# RADIO STATION ID MAPPINGS
# ==============================================================================

RADIO_TO_ID: dict[str, str] = {
    # Argentina
    "Radio Mitre": "mitre",
    "Radio Suquía": "suquia",
    "Radio Chubut": "chubut",
    "Radio Panorama": "panorama",
    # Bolivia
    "Radio Fides": "fides",
    "Radio Erbol": "erbol",
    # Chile
    "Radio Cooperativa": "cooperativa",
    "Radio ADN": "adn",
    "ADN": "adn",
    # Colombia
    "Caracol Radio": "caracol",
    "Caracol": "caracol",
    "RCN Radio": "rcn",
    # Costa Rica
    "Radio Columbia": "columbia",
    "Radio Monumental": "monumental",
    # Cuba
    "Radio Rebelde": "rebelde",
    # Dominican Republic
    "CDN Radio": "cdn",
    "Z101": "z101",
    # Ecuador
    "Radio Ecuadoradio": "ecuadoradio",
    "Radio Quito": "quito",
    "Teleamazonas Radio": "teleamazonas",
    # El Salvador
    "Radio YSU": "ysu",
    "Radio YSKL": "yskl",
    # Spain
    "Cadena SER": "ser",
    "Cadena Ser": "ser",
    "Cadena COPE": "cope",
    "Radio Nacional de España": "rne",
    "Radio Club Tenerife": "clubtenerife",
    "Radio Sevilla": "sevilla",
    # Guatemala
    "Emisoras Unidas": "emisorasunidas",
    # Honduras
    "HRN": "hrn",
    "Radio América": "america",
    # Mexico
    "Radio Fórmula": "formula",
    "MVS Noticias": "mvs",
    # Nicaragua
    "Radio Nicaragua": "radionicaragua",
    "Radio Corporación": "corporacion",
    # Panama
    "Radio Panamá": "radiopanama",
    "Radio ABC": "abc",
    # Paraguay
    "Radio Ñandutí": "nanduti",
    # Peru
    "RPP": "rpp",
    # Uruguay
    "Radio Sarandí": "sarandi",
    "Radio Carve": "carve",
    # USA (Miami)
    "Univision Radio": "univision",
    "Univision": "univision",
    # Venezuela
    "RCR": "rcr",
    "Radio Caracas Radio": "rcr",
}


def slugify(text: str) -> str:
    """Create a URL-safe slug from text."""
    import unicodedata
    import re
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    # Remove non-ASCII
    text = text.encode("ascii", "ignore").decode("ascii")
    # Replace spaces with hyphens and convert to lowercase
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "_", text)
    return text


def get_radio_id(radio_name: str) -> str:
    """Get standardized radio ID from radio name."""
    if radio_name in RADIO_TO_ID:
        return RADIO_TO_ID[radio_name]
    
    # Generate slug and warn
    radio_id = slugify(radio_name)
    logger.warning(f"Radio '{radio_name}' not in mapping, using generated ID: {radio_id}")
    return radio_id


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def seconds_to_hms(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    if not seconds or seconds < 0:
        return "00:00:00"
    hrs, remainder = divmod(int(seconds), 3600)
    mins, secs = divmod(remainder, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def get_alpha2_code(alpha3: str) -> str:
    """Get ISO 3166-1 alpha-2 code from alpha-3."""
    # Handle regional codes (e.g., ARG-CBA -> AR)
    base_code = alpha3.split("-")[0] if "-" in alpha3 else alpha3
    return ALPHA3_TO_ALPHA2.get(base_code, "")


def get_country_name(alpha3: str) -> str:
    """Get country name from alpha-3 code."""
    if alpha3 in ALPHA3_TO_NAME:
        return ALPHA3_TO_NAME[alpha3]
    # Try location from countries.py
    loc = get_location(alpha3)
    if loc:
        return loc.name_es.split(":")[0].strip()
    return alpha3


def get_all_json_files() -> list[Path]:
    """
    Get all JSON files from transcripts directory in deterministic order.
    Same pattern as database_creation_v3.py.
    """
    if not TRANSCRIPTS_DIR.exists():
        logger.error(f"Transcripts directory not found: {TRANSCRIPTS_DIR}")
        return []
    
    json_files = []
    
    # Sort country directories alphabetically
    countries = sorted([d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir()], 
                      key=lambda p: p.name)
    
    for country_dir in countries:
        # Skip hidden folders and non-country folders
        if country_dir.name.startswith("."):
            continue
        # Sort JSON files alphabetically within each country
        country_files = sorted(country_dir.glob("*.json"), 
                              key=lambda p: p.name)
        json_files.extend(country_files)
    
    logger.info(f"Found {len(json_files)} JSON files in {len(countries)} country folders")
    return json_files


def calculate_duration_and_words(data: dict) -> tuple[int, int]:
    """
    Calculate duration (seconds) and word count from transcript JSON.
    
    Returns:
        Tuple of (duration_seconds, words_transcribed)
    """
    max_end = 0.0
    word_count = 0
    
    segments = data.get("segments", [])
    if not segments:
        return 0, 0
    
    for seg in segments:
        words = seg.get("words", [])
        word_count += len(words)
        
        for word in words:
            # Try end (seconds) or end_ms (milliseconds)
            end = word.get("end", 0)
            if end == 0:
                end_ms = word.get("end_ms", 0)
                end = end_ms / 1000.0 if end_ms else 0
            
            if end > max_end:
                max_end = end
    
    return int(round(max_end)), word_count


# ==============================================================================
# RECORD SCHEMA DEFINITION
# ==============================================================================

RECORD_FIELDS = [
    "corapan_id",
    "file_id",
    "filename",
    "date",
    "country_code_alpha3",
    "country_code_alpha2",
    "country_name",
    "city",
    "radio",
    "radio_id",
    "duration_seconds",
    "duration_hms",
    "words_transcribed",
    "language",
    "modality",
    "revision",
    "annotation_method",
    "annotation_schema",
    "annotation_tool",
    "annotation_access",
    "access_rights_data",
    "access_rights_metadata",
    "rights_statement_data",
    "rights_statement_metadata",
    "source_stream_type",
    "institution",
    "corpus_version",
    "created_at",
]


def extract_record(data: dict, corpus_version: str, created_at: str) -> dict[str, Any]:
    """
    Extract standardized metadata record from transcript JSON.
    """
    # Basic fields from JSON
    file_id = data.get("file_id", "")
    filename = data.get("filename", "")
    date = data.get("date", "")
    country_code = data.get("country_code", "")
    city = data.get("city", "")
    radio = data.get("radio", "")
    revision = data.get("revision", "")
    
    # Normalize country code
    country_code_alpha3 = normalize_country_code(country_code)
    country_code_alpha2 = get_alpha2_code(country_code_alpha3)
    country_name = get_country_name(country_code_alpha3)
    
    # Radio ID
    radio_id = get_radio_id(radio) if radio else ""
    
    # Calculate duration and word count
    duration_seconds, words_transcribed = calculate_duration_and_words(data)
    duration_hms = seconds_to_hms(duration_seconds)
    
    # Construct corapan_id
    corapan_id = f"corapan:{country_code_alpha3}:{date}:{radio_id}"
    
    # Language - use es-XX variant based on country
    language = f"es-{country_code_alpha2}" if country_code_alpha2 else "es"
    
    # Fixed annotation metadata
    ann_meta = data.get("ann_meta", {})
    annotation_schema = ann_meta.get("version", "corapan-ann/v3")
    
    return {
        "corapan_id": corapan_id,
        "file_id": file_id,
        "filename": filename,
        "date": date,
        "country_code_alpha3": country_code_alpha3,
        "country_code_alpha2": country_code_alpha2,
        "country_name": country_name,
        "city": city,
        "radio": radio,
        "radio_id": radio_id,
        "duration_seconds": duration_seconds,
        "duration_hms": duration_hms,
        "words_transcribed": words_transcribed,
        "language": language,
        "modality": "spoken_broadcast",
        "revision": revision,
        "annotation_method": "Automatic (Amberscript) + Manual Correction",
        "annotation_schema": annotation_schema,
        "annotation_tool": "spaCy es_dep_news_trf + postprocessing (pastType/futureType)",
        "annotation_access": "restricted",
        "access_rights_data": "restricted",
        "access_rights_metadata": "open",
        "rights_statement_data": "Audio and transcript data are provided under restricted access due to copyright and privacy regulations; see project website for details.",
        "rights_statement_metadata": "Metadata released under CC-BY 4.0.",
        "source_stream_type": "online_stream_download",
        "institution": "Philipps-Universität Marburg",
        "corpus_version": corpus_version,
        "created_at": created_at,
    }


# ==============================================================================
# CORPUS-LEVEL METADATA
# ==============================================================================

def create_corpus_metadata(corpus_version: str, release_date: str, created_at: str) -> dict:
    """Create corpus-level metadata dictionary."""
    return {
        "title": "CO.RA.PAN – Corpus Radiofónico Panhispánico",
        "short_description_en": (
            "CO.RA.PAN is a spoken corpus of around 1.4 million words from radio news "
            "broadcasts of capital-city stations across almost all Spanish-speaking countries. "
            "It provides transcribed and linguistically annotated standard Spanish, enabling "
            "systematic research on the pluricentric nature of the language across the Hispanic world."
        ),
        "short_description_es": (
            "CO.RA.PAN es un corpus oral de aproximadamente 1,4 millones de palabras procedentes "
            "de noticiarios radiofónicos de emisoras de las capitales de casi todos los países "
            "hispanohablantes. Ofrece español estándar transcrito y anotado lingüísticamente, "
            "permitiendo la investigación sistemática sobre la naturaleza pluricéntrica del español."
        ),
        "creators": ["Felix Tacke and team, Philipps-Universität Marburg"],
        "funding": "Forschungsförderfonds der Philipps-Universität Marburg",
        "version": corpus_version,
        "release_date": release_date,
        "metadata_license": "CC-BY 4.0",
        "access_rights_data": "restricted",
        "access_rights_metadata": "open",
        "rights_statement_data": (
            "Audio and transcript data are provided under restricted access due to "
            "copyright and privacy regulations; see project website for details."
        ),
        "rights_statement_metadata": "Metadata released under CC-BY 4.0.",
        "contact_email": "felix.tacke@uni-marburg.de",
        "landing_page": "https://hispanistica.online.uni-marburg.de/corapan/",
        "doi": "",  # Placeholder for future DOI
        "zenodo_record": "",  # Placeholder for Zenodo
        "created_at": created_at,
    }


def create_corpus_metadata_jsonld(metadata: dict) -> dict:
    """Create JSON-LD version of corpus metadata with schema.org context."""
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "dc": "http://purl.org/dc/terms/",
            "datacite": "http://purl.org/datacite/v4.4/",
        },
        "@type": "Dataset",
        "@id": metadata.get("doi") or metadata.get("landing_page"),
        "name": metadata["title"],
        "description": metadata["short_description_en"],
        "version": metadata["version"],
        "datePublished": metadata["release_date"],
        "dateModified": metadata["created_at"],
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "creator": {
            "@type": "Organization",
            "name": "Philipps-Universität Marburg",
            "url": "https://www.uni-marburg.de/",
        },
        "author": [
            {
                "@type": "Person",
                "name": "Felix Tacke",
                "affiliation": "Philipps-Universität Marburg",
            }
        ],
        "funder": {
            "@type": "Organization",
            "name": "Forschungsförderfonds der Philipps-Universität Marburg",
        },
        "inLanguage": "es",
        "url": metadata["landing_page"],
        "distribution": [
            {
                "@type": "DataDownload",
                "encodingFormat": "application/json",
                "contentUrl": f"{metadata['landing_page']}data/public/metadata/latest/corapan_recordings.json",
            },
            {
                "@type": "DataDownload",
                "encodingFormat": "text/tab-separated-values",
                "contentUrl": f"{metadata['landing_page']}data/public/metadata/latest/corapan_recordings.tsv",
            },
        ],
        "keywords": [
            "Spanish corpus",
            "spoken language",
            "radio broadcast",
            "pluricentric Spanish",
            "linguistic annotation",
            "Hispanic linguistics",
        ],
    }


# ==============================================================================
# JSON-LD FOR RECORDINGS
# ==============================================================================

def record_to_jsonld(record: dict) -> dict:
    """Convert a recording record to JSON-LD format."""
    return {
        "@context": {
            "@vocab": "https://schema.org/",
            "dc": "http://purl.org/dc/terms/",
        },
        "@type": "AudioObject",
        "identifier": record["corapan_id"],
        "name": f"CO.RA.PAN – {record['country_name']}, {record['radio']}, {record['date']}",
        "dateCreated": record["date"],
        "duration": f"PT{record['duration_seconds']}S",
        "inLanguage": record["language"],
        "contentLocation": {
            "@type": "Place",
            "name": record["city"],
            "addressCountry": record["country_code_alpha2"],
        },
        "creator": {
            "@type": "Organization",
            "name": record["institution"],
        },
        "encodingFormat": "audio/mpeg",
        "license": "restricted",
        "accessMode": "auditory",
    }


# ==============================================================================
# TEI HEADER GENERATION
# ==============================================================================

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"


def create_tei_header(record: dict) -> str:
    """
    Create a TEI header XML for a recording.
    Returns pretty-printed XML string.
    """
    # Register namespace
    ET.register_namespace("", TEI_NAMESPACE)
    ET.register_namespace("xml", XML_NAMESPACE)
    
    # Root element
    tei = ET.Element(
        f"{{{TEI_NAMESPACE}}}TEI",
        attrib={f"{{{XML_NAMESPACE}}}lang": record["language"]}
    )
    
    # teiHeader
    header = ET.SubElement(tei, f"{{{TEI_NAMESPACE}}}teiHeader")
    
    # ---- fileDesc ----
    file_desc = ET.SubElement(header, f"{{{TEI_NAMESPACE}}}fileDesc")
    
    # titleStmt
    title_stmt = ET.SubElement(file_desc, f"{{{TEI_NAMESPACE}}}titleStmt")
    title = ET.SubElement(title_stmt, f"{{{TEI_NAMESPACE}}}title")
    title.text = f"CO.RA.PAN – {record['country_name']}, {record['radio']}, {record['date']}"
    
    resp_stmt = ET.SubElement(title_stmt, f"{{{TEI_NAMESPACE}}}respStmt")
    resp = ET.SubElement(resp_stmt, f"{{{TEI_NAMESPACE}}}resp")
    resp.text = "Corpus compilation and annotation"
    name = ET.SubElement(resp_stmt, f"{{{TEI_NAMESPACE}}}name")
    name.text = "Felix Tacke and team, Philipps-Universität Marburg"
    
    # publicationStmt
    pub_stmt = ET.SubElement(file_desc, f"{{{TEI_NAMESPACE}}}publicationStmt")
    publisher = ET.SubElement(pub_stmt, f"{{{TEI_NAMESPACE}}}publisher")
    publisher.text = "Philipps-Universität Marburg"
    
    availability = ET.SubElement(pub_stmt, f"{{{TEI_NAMESPACE}}}availability", status="restricted")
    licence = ET.SubElement(availability, f"{{{TEI_NAMESPACE}}}licence", target="https://creativecommons.org/licenses/by/4.0/")
    p_lic = ET.SubElement(licence, f"{{{TEI_NAMESPACE}}}p")
    p_lic.text = record["rights_statement_metadata"]
    p_data = ET.SubElement(availability, f"{{{TEI_NAMESPACE}}}p")
    p_data.text = record["rights_statement_data"]
    
    idno = ET.SubElement(pub_stmt, f"{{{TEI_NAMESPACE}}}idno", type="corapan-id")
    idno.text = record["corapan_id"]
    
    # sourceDesc
    source_desc = ET.SubElement(file_desc, f"{{{TEI_NAMESPACE}}}sourceDesc")
    recording_stmt = ET.SubElement(source_desc, f"{{{TEI_NAMESPACE}}}recordingStmt")
    recording = ET.SubElement(recording_stmt, f"{{{TEI_NAMESPACE}}}recording", type="broadcast")
    
    date_elem = ET.SubElement(recording, f"{{{TEI_NAMESPACE}}}date", when=record["date"])
    date_elem.text = record["date"]
    
    # Place with settlement and country
    place = ET.SubElement(recording, f"{{{TEI_NAMESPACE}}}placeName")
    settlement = ET.SubElement(place, f"{{{TEI_NAMESPACE}}}settlement")
    settlement.text = record["city"]
    country = ET.SubElement(place, f"{{{TEI_NAMESPACE}}}country", key=record["country_code_alpha3"])
    country.text = record["country_name"]
    
    # Broadcast
    broadcast = ET.SubElement(recording, f"{{{TEI_NAMESPACE}}}broadcast")
    broadcaster = ET.SubElement(broadcast, f"{{{TEI_NAMESPACE}}}broadcaster")
    broadcaster.text = record["radio"]
    
    # ---- encodingDesc ----
    encoding_desc = ET.SubElement(header, f"{{{TEI_NAMESPACE}}}encodingDesc")
    
    app_info = ET.SubElement(encoding_desc, f"{{{TEI_NAMESPACE}}}appInfo")
    application = ET.SubElement(app_info, f"{{{TEI_NAMESPACE}}}application", ident="corapan-annotation", version=record["annotation_schema"])
    app_label = ET.SubElement(application, f"{{{TEI_NAMESPACE}}}label")
    app_label.text = record["annotation_tool"]
    app_desc = ET.SubElement(application, f"{{{TEI_NAMESPACE}}}desc")
    app_desc.text = record["annotation_method"]
    
    project_desc = ET.SubElement(encoding_desc, f"{{{TEI_NAMESPACE}}}projectDesc")
    p_proj = ET.SubElement(project_desc, f"{{{TEI_NAMESPACE}}}p")
    p_proj.text = (
        "CO.RA.PAN is a spoken corpus of radio news broadcasts from Spanish-speaking countries. "
        "Transcriptions were created using Amberscript automatic speech recognition and manually corrected. "
        "Linguistic annotation was performed using spaCy with the es_dep_news_trf model."
    )
    
    # ---- profileDesc ----
    profile_desc = ET.SubElement(header, f"{{{TEI_NAMESPACE}}}profileDesc")
    
    lang_usage = ET.SubElement(profile_desc, f"{{{TEI_NAMESPACE}}}langUsage")
    language_elem = ET.SubElement(lang_usage, f"{{{TEI_NAMESPACE}}}language", ident=record["language"])
    language_elem.text = "Spanish"
    
    # Placeholder for participant descriptions
    particDesc = ET.SubElement(profile_desc, f"{{{TEI_NAMESPACE}}}particDesc")
    p_partic = ET.SubElement(particDesc, f"{{{TEI_NAMESPACE}}}p")
    p_partic.text = "Speaker information available in full corpus data."
    
    # Convert to pretty-printed string
    rough_string = ET.tostring(tei, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)


# ==============================================================================
# FILE WRITING FUNCTIONS
# ==============================================================================

def write_tsv(records: list[dict], output_path: Path) -> None:
    """Write records to TSV file."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RECORD_FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Written: {output_path}")


def write_json(data: Any, output_path: Path) -> None:
    """Write data to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Written: {output_path}")


def write_tei_files(records: list[dict], tei_dir: Path) -> None:
    """Write TEI header files for all recordings."""
    tei_dir.mkdir(parents=True, exist_ok=True)
    
    for record in records:
        # Sanitize corapan_id for filename (replace : with _)
        safe_id = record["corapan_id"].replace(":", "_")
        tei_path = tei_dir / f"{safe_id}.xml"
        
        try:
            tei_content = create_tei_header(record)
            with open(tei_path, "w", encoding="utf-8") as f:
                f.write(tei_content)
        except Exception as e:
            logger.error(f"Error writing TEI for {record['corapan_id']}: {e}")
    
    logger.info(f"Written {len(records)} TEI header files to {tei_dir}")


def create_tei_zip(tei_dir: Path, zip_path: Path) -> None:
    """Create ZIP archive of TEI files."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for tei_file in tei_dir.glob("*.xml"):
            zf.write(tei_file, arcname=tei_file.name)
    logger.info(f"Written: {zip_path}")


# ==============================================================================
# COUNTRY-LEVEL METADATA
# ==============================================================================

def write_country_metadata(records: list[dict], output_dir: Path) -> int:
    """
    Write country-level metadata files (TSV and JSON) for each country.
    
    Creates:
        - corapan_recordings_{COUNTRY_CODE}.tsv
        - corapan_recordings_{COUNTRY_CODE}.json
    
    Args:
        records: List of all recording records
        output_dir: Directory to write files to
        
    Returns:
        Number of countries processed
    """
    from collections import defaultdict
    
    # Group records by country code (alpha-3)
    by_country: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        country_code = record["country_code_alpha3"]
        if country_code:
            by_country[country_code].append(record)
    
    country_count = 0
    
    for country_code, country_records in sorted(by_country.items()):
        # Sort by date within country
        country_records.sort(key=lambda r: r["date"])
        
        # TSV file
        tsv_path = output_dir / f"corapan_recordings_{country_code}.tsv"
        write_tsv(country_records, tsv_path)
        
        # JSON file
        json_path = output_dir / f"corapan_recordings_{country_code}.json"
        write_json(country_records, json_path)
        
        country_count += 1
        logger.info(f"  {country_code}: {len(country_records)} recordings")
    
    logger.info(f"Written country-level metadata for {country_count} countries")
    return country_count


def update_latest_link(version_dir: Path, latest_path: Path) -> None:
    """Update the 'latest' symlink/junction to point to version_dir."""
    try:
        # Remove existing latest if present
        if latest_path.exists() or latest_path.is_symlink():
            if latest_path.is_symlink() or latest_path.is_file():
                latest_path.unlink()
            elif latest_path.is_dir():
                # On Windows, might be a junction or directory
                try:
                    latest_path.unlink()
                except OSError:
                    shutil.rmtree(latest_path)
        
        # Create new symlink (works on Windows with admin rights or developer mode)
        # Try symlink first
        try:
            latest_path.symlink_to(version_dir, target_is_directory=True)
            logger.info(f"Created symlink: {latest_path} -> {version_dir}")
        except OSError:
            # Fallback: copy directory on Windows without symlink support
            shutil.copytree(version_dir, latest_path)
            logger.info(f"Copied directory (symlink not supported): {version_dir} -> {latest_path}")
            
    except Exception as e:
        logger.error(f"Failed to update 'latest' link: {e}")
        raise


# ==============================================================================
# MAIN EXPORT FUNCTION
# ==============================================================================

def run_export(corpus_version: str, release_date: str) -> bool:
    """
    Main export function.
    
    Returns:
        True if export succeeded, False otherwise.
    """
    logger.info("=" * 80)
    logger.info("CO.RA.PAN Metadata Export")
    logger.info("=" * 80)
    logger.info(f"Corpus Version: {corpus_version}")
    logger.info(f"Release Date:   {release_date}")
    logger.info(f"Project Root:   {PROJECT_ROOT}")
    logger.info(f"Transcripts:    {TRANSCRIPTS_DIR}")
    logger.info(f"Metadata Root:  {PUBLIC_METADATA_DIR}")
    logger.info("=" * 80)
    
    # Validate inputs
    if not TRANSCRIPTS_DIR.exists():
        logger.error(f"Transcripts directory not found: {TRANSCRIPTS_DIR}")
        return False
    
    # Create version directory
    version_dir = PUBLIC_METADATA_DIR / f"v{release_date}"
    tei_dir = version_dir / "tei"
    
    try:
        version_dir.mkdir(parents=True, exist_ok=True)
        tei_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create output directories: {e}")
        return False
    
    # Timestamp for created_at
    created_at = datetime.now(timezone.utc).isoformat()
    
    # Get all JSON files
    json_files = get_all_json_files()
    if not json_files:
        logger.error("No JSON files found to process")
        return False
    
    # Process all files
    records = []
    success_count = 0
    error_count = 0
    
    logger.info("Processing transcript files...")
    
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            
            record = extract_record(data, corpus_version, created_at)
            records.append(record)
            success_count += 1
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {jf.name}: {e}")
            error_count += 1
        except Exception as e:
            logger.error(f"Error processing {jf.name}: {e}")
            error_count += 1
    
    if not records:
        logger.error("No records extracted successfully")
        return False
    
    # Sort records by country, then date
    records.sort(key=lambda r: (r["country_code_alpha3"], r["date"]))
    
    # Write recording metadata files
    logger.info("Writing metadata files...")
    
    # TSV
    write_tsv(records, version_dir / "corapan_recordings.tsv")
    
    # JSON
    write_json(records, version_dir / "corapan_recordings.json")
    
    # JSON-LD for recordings
    jsonld_records = [record_to_jsonld(r) for r in records]
    write_json(jsonld_records, version_dir / "corapan_recordings.jsonld")
    
    # Corpus-level metadata
    corpus_meta = create_corpus_metadata(corpus_version, release_date, created_at)
    write_json(corpus_meta, version_dir / "corapan_corpus_metadata.json")
    
    # Corpus-level JSON-LD
    corpus_meta_jsonld = create_corpus_metadata_jsonld(corpus_meta)
    write_json(corpus_meta_jsonld, version_dir / "corapan_corpus_metadata.jsonld")
    
    # TEI headers
    logger.info("Writing TEI header files...")
    write_tei_files(records, tei_dir)
    
    # Create TEI ZIP
    create_tei_zip(tei_dir, version_dir / "tei_headers.zip")
    
    # Country-level metadata
    logger.info("Writing country-level metadata files...")
    country_count = write_country_metadata(records, version_dir)
    
    # Update latest symlink
    latest_path = PUBLIC_METADATA_DIR / "latest"
    try:
        update_latest_link(version_dir, latest_path)
        latest_updated = True
    except Exception as e:
        logger.error(f"Failed to update 'latest': {e}")
        latest_updated = False
    
    # Summary
    logger.info("=" * 80)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"JSON files found:    {len(json_files)}")
    logger.info(f"Records exported:    {success_count}")
    logger.info(f"Countries:           {country_count}")
    logger.info(f"Errors:              {error_count}")
    logger.info(f"Output directory:    {version_dir}")
    logger.info(f"'latest' updated:    {'Yes' if latest_updated else 'No'}")
    logger.info("=" * 80)
    
    return True


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Export CO.RA.PAN metadata from transcript JSONs to FAIR-compliant formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python export_metadata.py --corpus-version v1.0 --release-date 2025-12-15
    python export_metadata.py -v v1.1 -d 2026-01-15
        """
    )
    
    parser.add_argument(
        "--corpus-version", "-v",
        required=True,
        help="Corpus version identifier (e.g., v1.0, v1.1)"
    )
    
    parser.add_argument(
        "--release-date", "-d",
        required=True,
        help="Release date in YYYY-MM-DD format (e.g., 2025-12-15)"
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.release_date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format: {args.release_date}. Use YYYY-MM-DD.")
        sys.exit(1)
    
    # Run export
    success = run_export(args.corpus_version, args.release_date)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
