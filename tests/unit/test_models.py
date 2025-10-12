"""
Unit tests for rmlib.models module.

Tests Pydantic data models for:
- Type validation
- Field constraints
- Enum validation
- Custom validators
- Property methods
"""

import pytest
from pydantic import ValidationError

from rmagent.rmlib.models import (
    Citation,
    Event,
    FactType,
    Family,
    MotherLabel,
    Name,
    NameType,
    OwnerType,
    ParentLabel,
    Person,
    Place,
    PlaceType,
    ProofLevel,
    Sex,
    Source,
)


class TestEnumerations:
    """Test enumeration types."""

    def test_sex_enum(self):
        """Test Sex enumeration values."""
        assert Sex.MALE == 0
        assert Sex.FEMALE == 1
        assert Sex.UNKNOWN == 2

    def test_name_type_enum(self):
        """Test NameType enumeration values."""
        assert NameType.NULL == 0
        assert NameType.MAIDEN == 4
        assert NameType.MARRIED == 5

    def test_owner_type_enum(self):
        """Test OwnerType enumeration values."""
        assert OwnerType.PERSON == 0
        assert OwnerType.FAMILY == 1
        assert OwnerType.EVENT == 2

    def test_proof_level_enum(self):
        """Test ProofLevel enumeration values."""
        assert ProofLevel.BLANK == 0
        assert ProofLevel.PROVEN == 1
        assert ProofLevel.DISPROVEN == 2
        assert ProofLevel.DISPUTED == 3


class TestPersonModel:
    """Test Person model."""

    def test_person_creation_minimal(self):
        """Test creating person with minimal required fields."""
        person = Person(PersonID=1, Sex=Sex.MALE)
        assert person.person_id == 1
        assert person.sex == Sex.MALE
        assert person.living is False
        assert person.parent_id == 0
        assert person.spouse_id == 0

    def test_person_creation_full(self):
        """Test creating person with all fields."""
        person = Person(
            PersonID=123,
            UniqueID="550e8400-e29b-41d4-a716-446655440000",
            Sex=Sex.FEMALE,
            ParentID=10,
            SpouseID=20,
            Color=5,
            Relate1=3,
            Relate2=2,
            Flags=1,
            Living=True,
            Bookmark=1,
            Note="Test note",
            UTCModDate=44993.9143704283,
        )
        assert person.person_id == 123
        assert person.sex == Sex.FEMALE
        assert person.parent_id == 10
        assert person.spouse_id == 20
        assert person.living is True
        assert person.color == 5
        assert person.relate1 == 3
        assert person.relate2 == 2

    def test_person_sex_validation(self):
        """Test sex field validation."""
        # Valid values
        Person(PersonID=1, Sex=0)
        Person(PersonID=1, Sex=1)
        Person(PersonID=1, Sex=2)

        # Invalid value
        with pytest.raises(ValidationError, match="Sex must be"):
            Person(PersonID=1, Sex=5)

    def test_person_color_validation(self):
        """Test color field range validation."""
        # Valid values
        Person(PersonID=1, Sex=0, Color=0)
        Person(PersonID=1, Sex=0, Color=27)

        # Invalid values
        with pytest.raises(ValidationError):
            Person(PersonID=1, Sex=0, Color=28)
        with pytest.raises(ValidationError):
            Person(PersonID=1, Sex=0, Color=-1)

    def test_person_living_conversion(self):
        """Test living field converts integer to boolean."""
        person1 = Person(PersonID=1, Sex=0, Living=0)
        assert person1.living is False

        person2 = Person(PersonID=2, Sex=1, Living=1)
        assert person2.living is True

    def test_person_field_aliases(self):
        """Test that field aliases work."""
        # Using alias names
        person = Person(PersonID=1, Sex=0, ParentID=10)
        assert person.person_id == 1
        assert person.parent_id == 10


class TestNameModel:
    """Test Name model."""

    def test_name_creation_minimal(self):
        """Test creating name with minimal fields."""
        name = Name(NameID=1, OwnerID=100)
        assert name.name_id == 1
        assert name.owner_id == 100
        assert name.is_primary is False
        assert name.name_type == NameType.NULL

    def test_name_creation_full(self):
        """Test creating name with all fields."""
        name = Name(
            NameID=1,
            OwnerID=100,
            Surname="Smith",
            Given="John",
            Prefix="Dr.",
            Suffix="Jr.",
            Nickname="Johnny",
            NameType=NameType.BIRTH,
            IsPrimary=True,
            IsPrivate=False,
            Proof=ProofLevel.PROVEN,
            BirthYear=1850,
            DeathYear=1920,
        )
        assert name.surname == "Smith"
        assert name.given == "John"
        assert name.prefix == "Dr."
        assert name.suffix == "Jr."
        assert name.is_primary is True
        assert name.name_type == NameType.BIRTH
        assert name.proof == ProofLevel.PROVEN

    def test_name_full_name_property(self):
        """Test full_name property."""
        # Complete name
        name1 = Name(NameID=1, OwnerID=1, Surname="Smith", Given="John", Prefix="Dr.", Suffix="Jr.")
        assert name1.full_name == "Dr. John Smith Jr."

        # Name without prefix/suffix
        name2 = Name(NameID=2, OwnerID=2, Surname="Doe", Given="Jane")
        assert name2.full_name == "Jane Doe"

        # Name with no data
        name3 = Name(NameID=3, OwnerID=3)
        assert name3.full_name == "Unknown"

    def test_name_type_validation(self):
        """Test name type validation."""
        name = Name(NameID=1, OwnerID=1, NameType=NameType.MARRIED)
        assert name.name_type == NameType.MARRIED

    def test_name_bool_conversion(self):
        """Test boolean field conversion."""
        name = Name(NameID=1, OwnerID=1, IsPrimary=1, IsPrivate=0)
        assert name.is_primary is True
        assert name.is_private is False


class TestEventModel:
    """Test Event model."""

    def test_event_creation_minimal(self):
        """Test creating event with minimal fields."""
        event = Event(EventID=1, EventType=1, OwnerType=OwnerType.PERSON, OwnerID=100)
        assert event.event_id == 1
        assert event.event_type == 1
        assert event.owner_type == OwnerType.PERSON
        assert event.owner_id == 100
        assert event.is_primary is False

    def test_event_creation_full(self):
        """Test creating event with all fields."""
        event = Event(
            EventID=10,
            EventType=1,
            OwnerType=OwnerType.PERSON,
            OwnerID=100,
            FamilyID=50,
            PlaceID=200,
            Date="D.+18500101..+00000000..",
            SortDate=18500101000000,
            IsPrimary=True,
            IsPrivate=False,
            Proof=ProofLevel.PROVEN,
            Details="Born in hospital",
            Note="Test note",
        )
        assert event.event_id == 10
        assert event.family_id == 50
        assert event.place_id == 200
        assert event.is_primary is True
        assert event.proof == ProofLevel.PROVEN

    def test_event_owner_type_validation(self):
        """Test owner type validation."""
        # Person event
        event1 = Event(EventID=1, EventType=1, OwnerType=0, OwnerID=100)
        assert event1.owner_type == OwnerType.PERSON

        # Family event
        event2 = Event(EventID=2, EventType=2, OwnerType=1, OwnerID=50)
        assert event2.owner_type == OwnerType.FAMILY


class TestPlaceModel:
    """Test Place model."""

    def test_place_creation_minimal(self):
        """Test creating place with minimal fields."""
        place = Place(PlaceID=1)
        assert place.place_id == 1
        assert place.place_type == PlaceType.PLACE

    def test_place_creation_full(self):
        """Test creating place with all fields."""
        place = Place(
            PlaceID=100,
            PlaceType=PlaceType.PLACE,
            Name="Chicago, Cook County, Illinois, USA",
            Normalized="Chicago, Cook, Illinois, United States",
            Latitude=418816670,
            Longitude=-876868960,
            LatLongExact=True,
            Note="Test note",
        )
        assert place.place_id == 100
        assert place.name == "Chicago, Cook County, Illinois, USA"
        assert place.latitude == 418816670
        assert place.lat_long_exact is True

    def test_place_coordinate_conversion(self):
        """Test latitude/longitude decimal conversion."""
        place = Place(PlaceID=1, Latitude=418816670, Longitude=-876868960)
        assert place.latitude_decimal == pytest.approx(41.881667, rel=1e-5)
        assert place.longitude_decimal == pytest.approx(-87.686896, rel=1e-5)

        # Test zero coordinates
        place2 = Place(PlaceID=2, Latitude=0, Longitude=0)
        assert place2.latitude_decimal is None
        assert place2.longitude_decimal is None


class TestSourceModel:
    """Test Source model."""

    def test_source_creation_minimal(self):
        """Test creating source with minimal fields."""
        source = Source(SourceID=1)
        assert source.source_id == 1
        assert source.template_id == 0
        assert source.is_private is False

    def test_source_creation_full(self):
        """Test creating source with all fields."""
        source = Source(
            SourceID=100,
            Name="1850 U.S. Census",
            RefNumber="M432",
            ActualText="Census record text",
            Comments="Test comments",
            TemplateID=15,
            Fields=b"\xef\xbb\xbf<Root><Fields></Fields></Root>",
        )
        assert source.source_id == 100
        assert source.name == "1850 U.S. Census"
        assert source.template_id == 15
        assert source.fields is not None


class TestCitationModel:
    """Test Citation model."""

    def test_citation_creation_minimal(self):
        """Test creating citation with minimal fields."""
        citation = Citation(CitationID=1, SourceID=100)
        assert citation.citation_id == 1
        assert citation.source_id == 100

    def test_citation_creation_full(self):
        """Test creating citation with all fields."""
        citation = Citation(
            CitationID=500,
            SourceID=100,
            CitationName="Page 123",
            Comments="Detail comments",
            RefNumber="123",
            Footnote="Custom footnote",
            Fields=b"\xef\xbb\xbf<Root><Fields><Field><Name>Page</Name><Value>123</Value></Field></Fields></Root>",
        )
        assert citation.citation_id == 500
        assert citation.source_id == 100
        assert citation.citation_name == "Page 123"


class TestFamilyModel:
    """Test Family model."""

    def test_family_creation_minimal(self):
        """Test creating family with minimal fields."""
        family = Family(FamilyID=1)
        assert family.family_id == 1
        assert family.father_id == 0
        assert family.mother_id == 0
        assert family.is_private is False

    def test_family_creation_full(self):
        """Test creating family with all fields."""
        family = Family(
            FamilyID=50,
            FatherID=100,
            MotherID=101,
            ChildID=200,
            FatherLabel=ParentLabel.HUSBAND,
            MotherLabel=MotherLabel.WIFE,
            Proof=ProofLevel.PROVEN,
            Note="Test note",
        )
        assert family.family_id == 50
        assert family.father_id == 100
        assert family.mother_id == 101
        assert family.father_label == ParentLabel.HUSBAND
        assert family.mother_label == MotherLabel.WIFE

    def test_family_custom_labels(self):
        """Test custom parent labels."""
        family = Family(
            FamilyID=1,
            FatherLabel=ParentLabel.OTHER,
            FatherLabelStr="Guardian",
            MotherLabel=MotherLabel.OTHER,
            MotherLabelStr="Guardian",
        )
        assert family.father_label == ParentLabel.OTHER
        assert family.father_label_str == "Guardian"


class TestFactTypeModel:
    """Test FactType model."""

    def test_fact_type_creation_minimal(self):
        """Test creating fact type with minimal fields."""
        fact = FactType(FactTypeID=1, OwnerType=OwnerType.PERSON, Name="Birth")
        assert fact.fact_type_id == 1
        assert fact.owner_type == OwnerType.PERSON
        assert fact.name == "Birth"

    def test_fact_type_creation_full(self):
        """Test creating fact type with all fields."""
        fact = FactType(
            FactTypeID=100,
            OwnerType=OwnerType.PERSON,
            Name="Custom Fact",
            Abbrev="CF",
            GedcomTag="EVEN",
            UseValue=True,
            UseDate=True,
            UsePlace=True,
            Sentence="[person] had [Desc]",
            Flags=-1,
        )
        assert fact.fact_type_id == 100
        assert fact.name == "Custom Fact"
        assert fact.gedcom_tag == "EVEN"
        assert fact.use_value is True

    def test_fact_type_bool_conversion(self):
        """Test boolean field conversion."""
        fact = FactType(FactTypeID=1, OwnerType=0, Name="Test", UseValue=1, UseDate=0, UsePlace=1)
        assert fact.use_value is True
        assert fact.use_date is False
        assert fact.use_place is True


class TestModelIntegration:
    """Integration tests for models."""

    def test_model_with_database_row(self):
        """Test creating model from database row-like dict."""
        # Simulate sqlite3.Row data
        row_data = {
            "PersonID": 1,
            "Sex": 0,
            "Living": 1,
            "ParentID": 0,
            "SpouseID": 0,
            "Color": 5,
            "Relate1": 0,
            "Relate2": 0,
            "Flags": 0,
            "Bookmark": 0,
            "UTCModDate": 44993.9143704283,
        }
        person = Person(**row_data)
        assert person.person_id == 1
        assert person.sex == Sex.MALE
        assert person.living is True

    def test_model_serialization(self):
        """Test model serialization to dict."""
        person = Person(PersonID=1, Sex=Sex.MALE, Living=True)
        data = person.model_dump()
        assert data["person_id"] == 1
        assert data["sex"] == Sex.MALE
        assert data["living"] is True

    def test_model_serialization_with_aliases(self):
        """Test model serialization with original field names."""
        person = Person(PersonID=1, Sex=Sex.MALE, Living=True)
        data = person.model_dump(by_alias=True)
        assert data["PersonID"] == 1
        assert data["Sex"] == Sex.MALE
        assert data["Living"] is True
