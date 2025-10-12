"""
RootsMagic BLOB Parsers

Parses XML BLOB data from RootsMagic database columns:
- SourceTable.Fields
- CitationTable.Fields
- SourceTemplateTable.FieldDefs

Reference:
- RM11_BLOB_SourceFields.md
- RM11_BLOB_CitationFields.md
- RM11_BLOB_SourceTemplateFieldDefs.md
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# BOM marker for UTF-8 encoded BLOBs
UTF8_BOM = b"\xef\xbb\xbf"


@dataclass
class TemplateField:
    """Represents a field definition in a source template."""

    name: str
    field_type: str  # Text, Name, Date, Place
    hint: str | None = None
    long_hint: str | None = None
    citation_field: bool = False  # True if stored in CitationTable.Fields


class BLOBParseError(Exception):
    """Raised when BLOB data cannot be parsed."""

    pass


def parse_source_fields(blob_data: bytes | None) -> dict[str, str]:
    """
    Parse SourceTable.Fields BLOB to extract field name-value pairs.

    Args:
        blob_data: Raw BLOB bytes from SourceTable.Fields column

    Returns:
        Dictionary mapping field names to values
        For free-form sources (TemplateID=0): {'Footnote': '...', 'ShortFootnote': '...', 'Bibliography': '...'}
        For template sources: {'Author': '...', 'Title': '...', etc.}

    Raises:
        BLOBParseError: If XML is malformed

    Example:
        >>> fields = parse_source_fields(blob_data)
        >>> fields['Author']
        'Smith, John'
    """
    if not blob_data:
        return {}

    try:
        # Decode UTF-8 with BOM if present
        xml_text = _decode_blob(blob_data)

        # Parse XML
        root = ET.fromstring(xml_text)

        # Extract field name-value pairs
        fields = {}
        for field in root.findall(".//Field"):
            name_elem = field.find("Name")
            value_elem = field.find("Value")

            if name_elem is not None and value_elem is not None:
                name = name_elem.text or ""
                value = value_elem.text or ""
                fields[name] = value

        return fields

    except ET.ParseError as e:
        logger.error(f"Failed to parse SourceTable.Fields BLOB: {e}")
        raise BLOBParseError(f"Invalid XML in SourceTable.Fields: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error parsing SourceTable.Fields: {e}")
        raise BLOBParseError(f"Error parsing SourceTable.Fields: {e}") from e


def parse_citation_fields(blob_data: bytes | None) -> dict[str, str]:
    """
    Parse CitationTable.Fields BLOB to extract field name-value pairs.

    CitationTable.Fields has the same XML structure as SourceTable.Fields.
    The most common field is 'Page' (present in 95.8% of citations).

    Args:
        blob_data: Raw BLOB bytes from CitationTable.Fields column

    Returns:
        Dictionary mapping field names to values
        Most commonly: {'Page': '123'}
        For Find-a-Grave: {'FaGGraveNumber': '...', 'FaGCemetery': '...', etc.}

    Raises:
        BLOBParseError: If XML is malformed

    Example:
        >>> fields = parse_citation_fields(blob_data)
        >>> fields['Page']
        '123'
    """
    # Citation fields use identical structure to source fields
    return parse_source_fields(blob_data)


def parse_template_field_defs(blob_data: bytes | None) -> list[TemplateField]:
    """
    Parse SourceTemplateTable.FieldDefs BLOB to extract template field definitions.

    Args:
        blob_data: Raw BLOB bytes from SourceTemplateTable.FieldDefs column

    Returns:
        List of TemplateField objects defining the template structure

    Raises:
        BLOBParseError: If XML is malformed

    Example:
        >>> fields = parse_template_field_defs(blob_data)
        >>> fields[0].name
        'Author'
        >>> fields[0].field_type
        'Name'
        >>> fields[0].citation_field
        False
    """
    if not blob_data:
        return []

    try:
        # Decode UTF-8 with BOM if present
        xml_text = _decode_blob(blob_data)

        # Parse XML
        root = ET.fromstring(xml_text)

        # Extract field definitions
        field_defs = []
        for field in root.findall(".//Field"):
            # Required fields
            name_elem = field.find("Name")
            type_elem = field.find("Type")

            if name_elem is None or type_elem is None:
                continue

            name = name_elem.text or ""
            field_type = type_elem.text or "Text"

            # Optional fields
            hint_elem = field.find("Hint")
            long_hint_elem = field.find("LongHint")
            citation_field_elem = field.find("CitationField")

            hint = hint_elem.text if hint_elem is not None else None
            long_hint = long_hint_elem.text if long_hint_elem is not None else None
            citation_field = (
                citation_field_elem.text == "True" if citation_field_elem is not None else False
            )

            field_defs.append(
                TemplateField(
                    name=name,
                    field_type=field_type,
                    hint=hint,
                    long_hint=long_hint,
                    citation_field=citation_field,
                )
            )

        return field_defs

    except ET.ParseError as e:
        logger.error(f"Failed to parse SourceTemplateTable.FieldDefs BLOB: {e}")
        raise BLOBParseError(f"Invalid XML in SourceTemplateTable.FieldDefs: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error parsing SourceTemplateTable.FieldDefs: {e}")
        raise BLOBParseError(f"Error parsing SourceTemplateTable.FieldDefs: {e}") from e


def _decode_blob(blob_data: bytes) -> str:
    """
    Decode BLOB data as UTF-8, handling BOM if present.

    Args:
        blob_data: Raw BLOB bytes

    Returns:
        Decoded UTF-8 string

    Note:
        RootsMagic BLOBs typically start with UTF-8 BOM (EF BB BF)
    """
    # Check for UTF-8 BOM and use utf-8-sig to handle it
    if blob_data.startswith(UTF8_BOM):
        return blob_data.decode("utf-8-sig")
    else:
        return blob_data.decode("utf-8")


def has_blob_data(blob_data: bytes | None) -> bool:
    """
    Check if BLOB data exists and is not empty.

    Args:
        blob_data: Raw BLOB bytes

    Returns:
        True if BLOB contains data
    """
    return blob_data is not None and len(blob_data) > 0


def is_freeform_source(fields: dict[str, str]) -> bool:
    """
    Check if source fields represent a free-form source (TemplateID=0).

    Free-form sources always have exactly 3 fields:
    - Footnote
    - ShortFootnote
    - Bibliography

    Args:
        fields: Parsed source fields dictionary

    Returns:
        True if this appears to be a free-form source
    """
    return (
        len(fields) == 3
        and "Footnote" in fields
        and "ShortFootnote" in fields
        and "Bibliography" in fields
    )


def get_citation_level_fields(template_fields: list[TemplateField]) -> list[str]:
    """
    Get list of field names that are stored in CitationTable.Fields.

    Args:
        template_fields: List of template field definitions

    Returns:
        List of field names where citation_field=True
    """
    return [f.name for f in template_fields if f.citation_field]


def get_source_level_fields(template_fields: list[TemplateField]) -> list[str]:
    """
    Get list of field names that are stored in SourceTable.Fields.

    Args:
        template_fields: List of template field definitions

    Returns:
        List of field names where citation_field=False
    """
    return [f.name for f in template_fields if not f.citation_field]
