"""
Unit tests for rmlib.parsers.blob_parser module.

Tests BLOB parsing for:
- SourceTable.Fields
- CitationTable.Fields
- SourceTemplateTable.FieldDefs
"""

import pytest

from rmtool.rmlib.parsers.blob_parser import (
    parse_source_fields,
    parse_citation_fields,
    parse_template_field_defs,
    has_blob_data,
    is_freeform_source,
    get_citation_level_fields,
    get_source_level_fields,
    BLOBParseError,
    TemplateField,
    UTF8_BOM,
)


class TestSourceFieldsParsing:
    """Test parsing SourceTable.Fields BLOBs."""

    def test_parse_empty_blob(self):
        """Test parsing empty/null BLOB."""
        assert parse_source_fields(None) == {}
        assert parse_source_fields(b'') == {}

    def test_parse_freeform_source(self):
        """Test parsing free-form source (TemplateID=0)."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Footnote</Name>
    <Value>Full citation text</Value>
  </Field>
  <Field>
    <Name>ShortFootnote</Name>
    <Value>Short citation</Value>
  </Field>
  <Field>
    <Name>Bibliography</Name>
    <Value>Bibliography entry</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        assert len(fields) == 3
        assert fields['Footnote'] == 'Full citation text'
        assert fields['ShortFootnote'] == 'Short citation'
        assert fields['Bibliography'] == 'Bibliography entry'

    def test_parse_template_source(self):
        """Test parsing template-based source."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Value>Smith, John</Value>
  </Field>
  <Field>
    <Name>Title</Name>
    <Value>Census Records</Value>
  </Field>
  <Field>
    <Name>PublicationDate</Name>
    <Value>1900</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        assert len(fields) == 3
        assert fields['Author'] == 'Smith, John'
        assert fields['Title'] == 'Census Records'
        assert fields['PublicationDate'] == '1900'

    def test_parse_blob_with_bom(self):
        """Test parsing BLOB with UTF-8 BOM."""
        xml = UTF8_BOM + b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Value>Smith, John</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        assert fields['Author'] == 'Smith, John'

    def test_parse_empty_values(self):
        """Test parsing fields with empty values."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Value></Value>
  </Field>
  <Field>
    <Name>Title</Name>
    <Value>Some Title</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        assert fields['Author'] == ''
        assert fields['Title'] == 'Some Title'

    def test_parse_html_entities(self):
        """Test parsing values with HTML entities."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Footnote</Name>
    <Value>&quot;Title&quot; &amp; &lt;i&gt;Subtitle&lt;/i&gt;</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        # XML parser automatically decodes entities
        assert '"Title" & <i>Subtitle</i>' in fields['Footnote']

    def test_parse_malformed_xml(self):
        """Test error handling for malformed XML."""
        malformed = b'<Root><Fields><Field><Name>Test</Field></Root>'

        with pytest.raises(BLOBParseError, match="Invalid XML"):
            parse_source_fields(malformed)

    def test_parse_no_fields(self):
        """Test parsing BLOB with no fields."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields></Fields></Root>'''

        fields = parse_source_fields(xml)
        assert len(fields) == 0


class TestCitationFieldsParsing:
    """Test parsing CitationTable.Fields BLOBs."""

    def test_parse_single_page_field(self):
        """Test parsing most common case: single Page field."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Page</Name>
    <Value>123</Value>
  </Field>
</Fields></Root>'''

        fields = parse_citation_fields(xml)
        assert len(fields) == 1
        assert fields['Page'] == '123'

    def test_parse_findagrave_citation(self):
        """Test parsing Find-a-Grave citation with many fields."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>FaGGraveNumber</Name>
    <Value>12345678</Value>
  </Field>
  <Field>
    <Name>FaGCemetery</Name>
    <Value>Oak Hill Cemetery</Value>
  </Field>
  <Field>
    <Name>FaGLocation</Name>
    <Value>Washington, D.C.</Value>
  </Field>
  <Field>
    <Name>FaGURL</Name>
    <Value>https://www.findagrave.com/memorial/12345678</Value>
  </Field>
</Fields></Root>'''

        fields = parse_citation_fields(xml)
        assert len(fields) == 4
        assert fields['FaGGraveNumber'] == '12345678'
        assert fields['FaGCemetery'] == 'Oak Hill Cemetery'
        assert fields['FaGLocation'] == 'Washington, D.C.'

    def test_citation_fields_same_structure_as_source(self):
        """Test that citation fields use same parsing as source fields."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>TestField</Name>
    <Value>TestValue</Value>
  </Field>
</Fields></Root>'''

        source_fields = parse_source_fields(xml)
        citation_fields = parse_citation_fields(xml)
        assert source_fields == citation_fields


class TestTemplateFieldDefsParsing:
    """Test parsing SourceTemplateTable.FieldDefs BLOBs."""

    def test_parse_empty_template(self):
        """Test parsing empty template."""
        assert parse_template_field_defs(None) == []
        assert parse_template_field_defs(b'') == []

    def test_parse_simple_template(self):
        """Test parsing template with basic fields."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Type>Name</Type>
    <Hint>Author name</Hint>
    <CitationField>False</CitationField>
  </Field>
  <Field>
    <Name>Title</Name>
    <Type>Text</Type>
    <Hint>Title of work</Hint>
    <CitationField>False</CitationField>
  </Field>
  <Field>
    <Name>Page</Name>
    <Type>Text</Type>
    <Hint>Page number</Hint>
    <CitationField>True</CitationField>
  </Field>
</Fields></Root>'''

        fields = parse_template_field_defs(xml)
        assert len(fields) == 3

        # Check first field
        assert fields[0].name == 'Author'
        assert fields[0].field_type == 'Name'
        assert fields[0].hint == 'Author name'
        assert fields[0].citation_field is False

        # Check citation-level field
        assert fields[2].name == 'Page'
        assert fields[2].citation_field is True

    def test_parse_field_types(self):
        """Test parsing different field types."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>TextField</Name>
    <Type>Text</Type>
    <CitationField>False</CitationField>
  </Field>
  <Field>
    <Name>NameField</Name>
    <Type>Name</Type>
    <CitationField>False</CitationField>
  </Field>
  <Field>
    <Name>DateField</Name>
    <Type>Date</Type>
    <CitationField>False</CitationField>
  </Field>
  <Field>
    <Name>PlaceField</Name>
    <Type>Place</Type>
    <CitationField>False</CitationField>
  </Field>
</Fields></Root>'''

        fields = parse_template_field_defs(xml)
        assert fields[0].field_type == 'Text'
        assert fields[1].field_type == 'Name'
        assert fields[2].field_type == 'Date'
        assert fields[3].field_type == 'Place'

    def test_parse_optional_fields(self):
        """Test parsing with optional hint fields."""
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Type>Name</Type>
    <Hint>Short hint</Hint>
    <LongHint>This is a longer hint with more details</LongHint>
    <CitationField>False</CitationField>
  </Field>
  <Field>
    <Name>Title</Name>
    <Type>Text</Type>
    <CitationField>False</CitationField>
  </Field>
</Fields></Root>'''

        fields = parse_template_field_defs(xml)
        assert fields[0].hint == 'Short hint'
        assert fields[0].long_hint == 'This is a longer hint with more details'
        assert fields[1].hint is None
        assert fields[1].long_hint is None

    def test_parse_with_bom(self):
        """Test parsing template with UTF-8 BOM."""
        xml = UTF8_BOM + b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Type>Name</Type>
    <CitationField>False</CitationField>
  </Field>
</Fields></Root>'''

        fields = parse_template_field_defs(xml)
        assert len(fields) == 1
        assert fields[0].name == 'Author'

    def test_parse_malformed_template(self):
        """Test error handling for malformed template XML."""
        malformed = b'<Root><Fields><Field><Name>Test</Field></Root>'

        with pytest.raises(BLOBParseError, match="Invalid XML"):
            parse_template_field_defs(malformed)


class TestHelperFunctions:
    """Test helper functions."""

    def test_has_blob_data(self):
        """Test has_blob_data function."""
        assert has_blob_data(None) is False
        assert has_blob_data(b'') is False
        assert has_blob_data(b'<xml>test</xml>') is True

    def test_is_freeform_source(self):
        """Test is_freeform_source function."""
        # Freeform source has exactly 3 fields
        freeform = {
            'Footnote': 'text',
            'ShortFootnote': 'text',
            'Bibliography': 'text'
        }
        assert is_freeform_source(freeform) is True

        # Template source has different fields
        template = {
            'Author': 'Smith',
            'Title': 'Book'
        }
        assert is_freeform_source(template) is False

        # Missing one field
        incomplete = {
            'Footnote': 'text',
            'ShortFootnote': 'text'
        }
        assert is_freeform_source(incomplete) is False

    def test_get_citation_level_fields(self):
        """Test get_citation_level_fields function."""
        fields = [
            TemplateField('Author', 'Name', citation_field=False),
            TemplateField('Title', 'Text', citation_field=False),
            TemplateField('Page', 'Text', citation_field=True),
            TemplateField('ItemOfInterest', 'Text', citation_field=True),
        ]

        citation_fields = get_citation_level_fields(fields)
        assert citation_fields == ['Page', 'ItemOfInterest']

    def test_get_source_level_fields(self):
        """Test get_source_level_fields function."""
        fields = [
            TemplateField('Author', 'Name', citation_field=False),
            TemplateField('Title', 'Text', citation_field=False),
            TemplateField('Page', 'Text', citation_field=True),
        ]

        source_fields = get_source_level_fields(fields)
        assert source_fields == ['Author', 'Title']


class TestRealWorldExamples:
    """Test with real-world examples from RootsMagic databases."""

    def test_book_source(self):
        """Test typical book source."""
        xml = UTF8_BOM + b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Author</Name>
    <Value>Jones, Henry Z., Jr.</Value>
  </Field>
  <Field>
    <Name>Title</Name>
    <Value>The Palatine Families of New York</Value>
  </Field>
  <Field>
    <Name>PublicationFacts</Name>
    <Value>Universal City, California : H. Z. Jones, 1985</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        assert fields['Author'] == 'Jones, Henry Z., Jr.'
        assert fields['Title'] == 'The Palatine Families of New York'
        assert 'Universal City' in fields['PublicationFacts']

    def test_census_citation(self):
        """Test typical census citation."""
        xml = UTF8_BOM + b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>Page</Name>
    <Value>Sheet 15A</Value>
  </Field>
</Fields></Root>'''

        fields = parse_citation_fields(xml)
        assert fields['Page'] == 'Sheet 15A'

    def test_online_database_source(self):
        """Test online database source."""
        xml = UTF8_BOM + b'''<?xml version="1.0" encoding="UTF-8"?>
<Root><Fields>
  <Field>
    <Name>WebsiteTitle</Name>
    <Value>FamilySearch</Value>
  </Field>
  <Field>
    <Name>URL</Name>
    <Value>https://www.familysearch.org</Value>
  </Field>
  <Field>
    <Name>AccessDate</Name>
    <Value>15 Dec 2024</Value>
  </Field>
</Fields></Root>'''

        fields = parse_source_fields(xml)
        assert fields['WebsiteTitle'] == 'FamilySearch'
        assert fields['URL'] == 'https://www.familysearch.org'
        assert fields['AccessDate'] == '15 Dec 2024'
