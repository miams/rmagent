"""
Pydantic data models for RootsMagic database entities.

These models represent the core database tables with proper type hints,
validation, and documentation. They are used throughout the application
for type safety and data validation.

Reference: RM11_Schema_Reference.md, RM11_DataDef.yaml
"""

from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Enumerations


class Sex(IntEnum):
    """Person sex/gender."""

    MALE = 0
    FEMALE = 1
    UNKNOWN = 2


class NameType(IntEnum):
    """Type of name (primary, alternate, etc.)."""

    NULL = 0
    AKA = 1
    BIRTH = 2
    IMMIGRANT = 3
    MAIDEN = 4
    MARRIED = 5
    NICKNAME = 6
    OTHER_SPELLING = 7


class OwnerType(IntEnum):
    """Entity type for polymorphic relationships."""

    PERSON = 0
    FAMILY = 1
    EVENT = 2
    SOURCE = 3
    CITATION = 4
    PLACE = 5
    TASK = 6
    NAME = 7
    PLACE_DETAIL = 14
    ASSOCIATION = 19


class PlaceType(IntEnum):
    """Type of place entry."""

    PLACE = 0
    LDS_TEMPLE = 1
    PLACE_DETAIL = 2


class ProofLevel(IntEnum):
    """Evidence quality rating."""

    BLANK = 0
    PROVEN = 1
    DISPROVEN = 2
    DISPUTED = 3


class ParentLabel(IntEnum):
    """Label for parent in family."""

    FATHER = 0
    HUSBAND = 1
    PARTNER = 2
    OTHER = 99


class MotherLabel(IntEnum):
    """Label for mother in family."""

    MOTHER = 0
    WIFE = 1
    PARTNER = 2
    OTHER = 99


# Base Models


class RMBaseModel(BaseModel):
    """Base model for all RootsMagic entities with common fields."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=False,
        arbitrary_types_allowed=True,
        populate_by_name=True,  # Allow both alias and field name
    )

    utc_mod_date: float | None = Field(
        None, alias="UTCModDate", description="Last modification date (Julian day format)"
    )


# Core Entity Models


class Person(RMBaseModel):
    """
    Represents a person in the genealogy database.

    Reference: PersonTable in RM11_Schema_Reference.md
    """

    person_id: int = Field(..., alias="PersonID", description="Unique person identifier")
    unique_id: str | None = Field(
        None, alias="UniqueID", description="36-character hexadecimal unique ID"
    )
    sex: Sex = Field(..., alias="Sex", description="Person's sex/gender")
    parent_id: int = Field(0, alias="ParentID", description="FamilyID of parents (0 = no parents)")
    spouse_id: int = Field(0, alias="SpouseID", description="FamilyID of spouse (0 = no spouse)")
    color: int = Field(
        0, alias="Color", ge=0, le=27, description="Color coding (0=None, 1-27=specific colors)"
    )
    relate1: int = Field(
        0, ge=0, le=999, alias="Relate1", description="Generations to Most Recent Common Ancestor"
    )
    relate2: int = Field(
        0, ge=0, alias="Relate2", description="Generations from reference person to MRCA"
    )
    flags: int = Field(0, ge=0, le=10, alias="Flags", description="Relationship prefix descriptor")
    living: bool = Field(False, alias="Living", description="True if person is living")
    is_private: int = Field(0, alias="IsPrivate", description="Privacy flag (not implemented)")
    proof: int = Field(0, alias="Proof", description="Proof level (not implemented)")
    bookmark: int = Field(
        0, alias="Bookmark", description="Bookmark flag (0=not bookmarked, 1=bookmarked)"
    )
    note: str | None = Field(None, alias="Note", description="User-defined notes")

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, v):
        """Validate sex is in valid range."""
        if isinstance(v, int) and v not in [0, 1, 2]:
            raise ValueError(f"Sex must be 0 (Male), 1 (Female), or 2 (Unknown), got {v}")
        return v

    @field_validator("living", mode="before")
    @classmethod
    def convert_living_to_bool(cls, v):
        """Convert integer living flag to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v


class Name(RMBaseModel):
    """
    Represents a name for a person (primary or alternate).

    Reference: NameTable in RM11_Schema_Reference.md
    """

    name_id: int = Field(..., alias="NameID", description="Unique name identifier")
    owner_id: int = Field(..., alias="OwnerID", description="PersonID this name belongs to")
    surname: str | None = Field(None, alias="Surname", description="Surname/family name")
    given: str | None = Field(None, alias="Given", description="Given/first name")
    prefix: str | None = Field(None, alias="Prefix", description="Name prefix (Dr., Rev., etc.)")
    suffix: str | None = Field(
        None, alias="Suffix", description="Name suffix (Jr., Sr., III, etc.)"
    )
    nickname: str | None = Field(None, alias="Nickname", description="Nickname")
    name_type: NameType = Field(NameType.NULL, alias="NameType", description="Type of name")
    date: str | None = Field(
        None, alias="Date", description="Date associated with this name (24-char encoded)"
    )
    sort_date: int | None = Field(
        None,
        alias="SortDate",
        description="Sortable date representation (9223372036854775807 = unknown)",
    )
    is_primary: bool = Field(
        False, alias="IsPrimary", description="True if this is the primary name"
    )
    is_private: bool = Field(False, alias="IsPrivate", description="True if name is private")
    proof: ProofLevel = Field(
        ProofLevel.BLANK, alias="Proof", description="Evidence quality rating"
    )
    sentence: str | None = Field(None, alias="Sentence", description="Custom sentence template")
    note: str | None = Field(None, alias="Note", description="User-defined notes")
    birth_year: int | None = Field(
        None, alias="BirthYear", description="Year extracted from birth event"
    )
    death_year: int | None = Field(
        None, alias="DeathYear", description="Year extracted from death event"
    )
    surname_mp: str | None = Field(
        None, alias="SurnameMP", description="Metaphone encoding of surname"
    )
    given_mp: str | None = Field(
        None, alias="GivenMP", description="Metaphone encoding of given name"
    )
    nickname_mp: str | None = Field(
        None, alias="NicknameMP", description="Metaphone encoding of nickname"
    )

    @field_validator("is_primary", "is_private", mode="before")
    @classmethod
    def convert_bool_flags(cls, v):
        """Convert integer flags to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v

    @property
    def full_name(self) -> str:
        """Get formatted full name."""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        if self.given:
            parts.append(self.given)
        if self.surname:
            parts.append(self.surname)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts) if parts else "Unknown"


class Event(RMBaseModel):
    """
    Represents a life event or fact.

    Reference: EventTable in RM11_Schema_Reference.md
    """

    event_id: int = Field(..., alias="EventID", description="Unique event identifier")
    event_type: int = Field(..., alias="EventType", description="FactTypeID from FactTypeTable")
    owner_type: OwnerType = Field(
        ..., alias="OwnerType", description="Type of owner (person or family)"
    )
    owner_id: int = Field(..., alias="OwnerID", description="PersonID or FamilyID")
    family_id: int = Field(
        0, alias="FamilyID", description="FamilyID for parent-related events (0 = not applicable)"
    )
    place_id: int = Field(0, alias="PlaceID", description="PlaceID (0 = no place)")
    site_id: int = Field(0, alias="SiteID", description="PlaceID of place details (0 = no details)")
    date: str | None = Field(None, alias="Date", description="Date in 24-character encoded format")
    sort_date: int | None = Field(
        None, alias="SortDate", description="Sortable date representation"
    )
    is_primary: bool = Field(
        False, alias="IsPrimary", description="True if this is primary event (suppresses conflicts)"
    )
    is_private: bool = Field(False, alias="IsPrivate", description="True if event is private")
    proof: ProofLevel = Field(
        ProofLevel.BLANK, alias="Proof", description="Evidence quality rating"
    )
    status: int = Field(0, alias="Status", description="LDS status (0=default, 1-12=LDS statuses)")
    sentence: str | None = Field(None, alias="Sentence", description="Custom sentence template")
    details: str | None = Field(None, alias="Details", description="Event details/description")
    note: str | None = Field(None, alias="Note", description="User-defined notes")

    @field_validator("is_primary", "is_private", mode="before")
    @classmethod
    def convert_bool_flags(cls, v):
        """Convert integer flags to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v


class Place(RMBaseModel):
    """
    Represents a geographic place.

    Reference: PlaceTable in RM11_Schema_Reference.md
    """

    place_id: int = Field(..., alias="PlaceID", description="Unique place identifier")
    place_type: PlaceType = Field(
        PlaceType.PLACE, alias="PlaceType", description="Type of place entry"
    )
    name: str | None = Field(
        None, alias="Name", description="Place name (comma-delimited hierarchy)"
    )
    abbrev: str | None = Field(None, alias="Abbrev", description="Abbreviated place name")
    normalized: str | None = Field(None, alias="Normalized", description="Standardized place name")
    latitude: int = Field(0, alias="Latitude", description="Latitude (decimal degrees × 1e7)")
    longitude: int = Field(0, alias="Longitude", description="Longitude (decimal degrees × 1e7)")
    lat_long_exact: bool = Field(
        False, alias="LatLongExact", description="True if coordinates are exact"
    )
    master_id: int = Field(0, alias="MasterID", description="PlaceID of master place (for details)")
    note: str | None = Field(None, alias="Note", description="User-defined notes")
    reverse: str | None = Field(
        None, alias="Reverse", description="Reverse order of place hierarchy (for indexing)"
    )
    fs_id: int | None = Field(None, alias="fsID", description="FamilySearch place ID")
    an_id: int | None = Field(None, alias="anID", description="Ancestry.com place ID")

    @field_validator("lat_long_exact", mode="before")
    @classmethod
    def convert_bool_flag(cls, v):
        """Convert integer flag to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v

    @property
    def latitude_decimal(self) -> float | None:
        """Get latitude as decimal degrees."""
        if self.latitude and self.latitude != 0:
            return self.latitude / 1e7
        return None

    @property
    def longitude_decimal(self) -> float | None:
        """Get longitude as decimal degrees."""
        if self.longitude and self.longitude != 0:
            return self.longitude / 1e7
        return None


class Source(RMBaseModel):
    """
    Represents a source document.

    Reference: SourceTable in RM11_Schema_Reference.md
    """

    source_id: int = Field(..., alias="SourceID", description="Unique source identifier")
    name: str | None = Field(None, alias="Name", description="Source name")
    ref_number: str | None = Field(None, alias="RefNumber", description="Source reference number")
    actual_text: str | None = Field(None, alias="ActualText", description="Source text")
    comments: str | None = Field(None, alias="Comments", description="Source comments")
    is_private: bool = Field(False, alias="IsPrivate", description="True if source is private")
    template_id: int = Field(0, alias="TemplateID", description="SourceTemplateID (0=free-form)")
    fields: bytes | None = Field(
        None, alias="Fields", description="XML BLOB with field values (UTF-8 with BOM)"
    )

    @field_validator("is_private", mode="before")
    @classmethod
    def convert_bool_flag(cls, v):
        """Convert integer flag to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v


class Citation(RMBaseModel):
    """
    Represents a citation of a source.

    Reference: CitationTable in RM11_Schema_Reference.md
    """

    citation_id: int = Field(..., alias="CitationID", description="Unique citation identifier")
    source_id: int = Field(..., alias="SourceID", description="SourceID this citation references")
    comments: str | None = Field(None, alias="Comments", description="Detail comment")
    actual_text: str | None = Field(None, alias="ActualText", description="Research note")
    ref_number: str | None = Field(None, alias="RefNumber", description="Detail reference number")
    footnote: str | None = Field(None, alias="Footnote", description="Custom footnote override")
    short_footnote: str | None = Field(
        None, alias="ShortFootnote", description="Custom short footnote override"
    )
    bibliography: str | None = Field(
        None, alias="Bibliography", description="Custom bibliography override"
    )
    fields: bytes | None = Field(
        None, alias="Fields", description="XML BLOB with citation field values (UTF-8 with BOM)"
    )
    citation_name: str | None = Field(
        None, alias="CitationName", description="Auto-generated or user-defined name"
    )


class Family(RMBaseModel):
    """
    Represents a family unit (marriage/partnership).

    Reference: FamilyTable in RM11_Schema_Reference.md
    """

    family_id: int = Field(..., alias="FamilyID", description="Unique family identifier")
    father_id: int = Field(0, alias="FatherID", description="PersonID of father/husband/partner")
    mother_id: int = Field(0, alias="MotherID", description="PersonID of mother/wife/partner")
    child_id: int = Field(0, alias="ChildID", description="PersonID of root child (0=no children)")
    husb_order: int = Field(0, alias="HusbOrder", description="Spouse order (0=never rearranged)")
    wife_order: int = Field(0, alias="WifeOrder", description="Spouse order (0=never rearranged)")
    is_private: bool = Field(False, alias="IsPrivate", description="True if family is private")
    proof: ProofLevel = Field(
        ProofLevel.BLANK, alias="Proof", description="Evidence quality rating"
    )
    father_label: ParentLabel = Field(
        ParentLabel.FATHER, alias="FatherLabel", description="Label for father role"
    )
    mother_label: MotherLabel = Field(
        MotherLabel.MOTHER, alias="MotherLabel", description="Label for mother role"
    )
    father_label_str: str | None = Field(
        None, alias="FatherLabelStr", description="Custom label when FatherLabel=99"
    )
    mother_label_str: str | None = Field(
        None, alias="MotherLabelStr", description="Custom label when MotherLabel=99"
    )
    note: str | None = Field(None, alias="Note", description="User-defined notes")

    @field_validator("is_private", mode="before")
    @classmethod
    def convert_bool_flag(cls, v):
        """Convert integer flag to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v


class FactType(RMBaseModel):
    """
    Represents a fact/event type definition.

    Reference: FactTypeTable in RM11_Schema_Reference.md
    """

    fact_type_id: int = Field(
        ...,
        alias="FactTypeID",
        description="Unique fact type identifier (<1000=built-in, ≥1000=custom)",
    )
    owner_type: OwnerType = Field(
        ..., alias="OwnerType", description="Type of owner (person or family)"
    )
    name: str = Field(..., alias="Name", description="Fact type name")
    abbrev: str | None = Field(None, alias="Abbrev", description="Abbreviation")
    gedcom_tag: str | None = Field(None, alias="GedcomTag", description="GEDCOM tag")
    use_value: bool = Field(
        False, alias="UseValue", description="True if fact uses description field"
    )
    use_date: bool = Field(True, alias="UseDate", description="True if fact uses date field")
    use_place: bool = Field(True, alias="UsePlace", description="True if fact uses place field")
    sentence: str | None = Field(None, alias="Sentence", description="Sentence template")
    flags: int = Field(
        0, alias="Flags", description="6-bit position-coded flags for Include settings"
    )

    @field_validator("use_value", "use_date", "use_place", mode="before")
    @classmethod
    def convert_bool_flags(cls, v):
        """Convert integer flags to boolean."""
        if isinstance(v, int):
            return bool(v)
        return v
