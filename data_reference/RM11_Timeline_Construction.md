# RootsMagic 11: Timeline Construction Rules

**Document Version:** 1.0
**Last Updated:** 2025-01-08
**Target Format:** TimelineJS3 (https://timeline.knightlab.com)
**Purpose:** Define rules for constructing chronological timelines from RootsMagic data

---

## Overview

This document defines how to extract and format events from a RootsMagic database to create biographical timelines. The output format is **TimelineJS3 JSON**, enabling rich, interactive timeline visualization with dates, places, media, and narratives.

### Timeline Use Cases

1. **Personal Biography Timeline** - One person's life events
2. **Family Timeline** - Multiple family members' events combined
3. **Multi-Generational Timeline** - Ancestors and descendants
4. **Research Timeline** - Document discovery and analysis chronology

---

## TimelineJS3 JSON Structure

### Root Object

```json
{
  "title": {
    "text": {
      "headline": "Person Name",
      "text": "Brief biography or tagline"
    },
    "media": {
      "url": "path/to/photo.jpg",
      "caption": "Caption text",
      "credit": "Photo credit"
    }
  },
  "events": [
    // Array of event objects
  ],
  "eras": [
    // Optional background eras
  ],
  "scale": "human"
}
```

---

### Event Object Structure

```json
{
  "start_date": {
    "year": 1921,
    "month": 12,
    "day": 30,
    "display_date": "December 30, 1921"
  },
  "end_date": {
    // Optional, for date ranges
  },
  "text": {
    "headline": "Birth",
    "text": "<p>John Dorsey Iams was born in Tulsa, Oklahoma.</p>"
  },
  "media": {
    "url": "path/to/media.jpg",
    "caption": "Caption text",
    "credit": "Source citation"
  },
  "group": "Early Life",
  "background": {
    "color": "#f4f4f4"
  },
  "unique_id": "event_1_1872"
}
```

---

## Event Extraction Rules

### Rule 1: Event Selection

**Include Events:**
- All vital events (Birth, Death, Baptism, Burial)
- Major life events (Marriage, Education, Occupation)
- Migration events (Immigration, Emigration, Residence)
- Significant historical events (Census, Military service)
- Events with dates and/or significant details

**Exclude Events:**
- Events marked `IsPrivate = 1` (unless generating private timeline)
- Events without dates AND without meaningful details
- Duplicate events (same type, same date)
- Technical events (SSN, AFN, Reference numbers)

**SQL Query:**
```sql
SELECT
    e.EventID,
    ft.Name as EventType,
    e.Date,
    e.SortDate,
    e.Details,
    pl.Name as Place,
    e.IsPrivate,
    e.Proof
FROM EventTable e
JOIN FactTypeTable ft ON e.EventType = ft.FactTypeID
LEFT JOIN PlaceTable pl ON e.PlaceID = pl.PlaceID
WHERE e.OwnerType = 0
  AND e.OwnerID = ?  -- PersonID
  AND e.IsPrivate = 0  -- Exclude private
  AND e.EventType NOT IN (30, 34, 35)  -- Exclude SSN, AFN, Ref#
ORDER BY e.SortDate;
```

---

### Rule 2: Chronological Ordering

**Sort Events By:**
1. **SortDate** (primary) - Integer representation of date
2. **EventType priority** (secondary) - For same-date events
3. **EventID** (tertiary) - For identical events

**Same-Date Event Priority:**
```
1. Birth (1)
2. Death (2)
3. Marriage (300)
4. Other events (by EventType ID)
```

**Unknown Date Handling:**
- `SortDate = 9223372036854775807` = Unknown/missing date
- Place at end of timeline OR in separate "Undated Events" section
- Label as "Date Unknown" in display

---

### Rule 3: Date Parsing

RootsMagic uses a 24-character encoded date format. Convert to TimelineJS3 date object.

#### Parse RM11 Date to TimelineJS3

**RootsMagic Date Format:** See RM11_Date_Format.md

**Conversion Rules:**

| RM11 Position | Content | TimelineJS3 Field |
|---------------|---------|-------------------|
| 4-7 | Year (yyyy) | `year` (number) |
| 8-9 | Month (mm) | `month` (1-12) |
| 10-11 | Day (dd) | `day` (1-31) |
| Full Date string | Original | `display_date` (optional) |

**Python Conversion:**
```python
def parse_rm_date_to_timelinejs(rm_date):
    """
    Convert RootsMagic 24-char date to TimelineJS3 date object.

    Args:
        rm_date: 24-character RM date string

    Returns:
        dict: TimelineJS3 date object
    """
    if not rm_date or rm_date == '.' or len(rm_date) < 24:
        return None

    # Extract components
    date_type = rm_date[0]  # D=standard, R=range, etc.
    modifier = rm_date[1]    # ., B=before, A=after, etc.
    era = rm_date[2]         # +/- for AD/BC
    year_str = rm_date[3:7]
    month_str = rm_date[7:9]
    day_str = rm_date[9:11]
    qualifier = rm_date[12]  # A=about, E=estimated, etc.

    # Parse year
    try:
        year = int(year_str)
        if era == '-':  # BC
            year = -year
    except:
        return None

    # Parse month (00 = unknown)
    month = None
    if month_str != '00':
        try:
            month = int(month_str)
        except:
            pass

    # Parse day (00 = unknown)
    day = None
    if day_str != '00':
        try:
            day = int(day_str)
        except:
            pass

    # Build date object
    date_obj = {"year": year}

    if month:
        date_obj["month"] = month

    if day:
        date_obj["day"] = day

    # Add display date for modifiers/qualifiers
    if modifier != '.' or qualifier != '.':
        date_obj["display_date"] = format_display_date(
            year, month, day, modifier, qualifier
        )

    return date_obj

def format_display_date(year, month, day, modifier, qualifier):
    """Format human-readable display date."""
    # Start with base date
    if day and month:
        base = f"{month}/{day}/{year}"
    elif month:
        base = f"{month}/{year}"
    else:
        base = str(year)

    # Add modifiers
    prefixes = {
        'B': 'Before ',
        'A': 'After ',
        'U': 'Until ',
        'F': 'From ',
        'T': 'To '
    }

    qualifiers_map = {
        'A': 'About ',
        'C': 'Calculated ',
        'E': 'Estimated ',
        '?': 'Possibly ',
        '1': 'Probably ',
        '2': 'Likely ',
        '3': 'Apparently ',
        '4': 'Perhaps ',
        '5': 'Maybe ',
        '6': 'Possibly '
    }

    result = ""
    if modifier in prefixes:
        result += prefixes[modifier]

    if qualifier in qualifiers_map:
        result += qualifiers_map[qualifier]

    result += base
    return result
```

---

### Rule 4: Date Range Handling

Some events have date ranges (e.g., "Between 1850 and 1860").

**Detection:**
- RM Date starts with `R` (range)
- RM Date starts with `S` (from date)
- RM Date starts with `T` (to date)

**TimelineJS3 Handling:**

```python
def parse_date_range(rm_date):
    """Parse date range into start_date and end_date."""
    date_type = rm_date[0]

    if date_type == 'R':  # Range: Between X and Y
        # RM stores: R.+YYYY1MM1DD1/+YYYY2MM2DD2
        # Split on '/'
        parts = rm_date.split('/')
        if len(parts) == 2:
            start_date = parse_rm_date_to_timelinejs('D' + parts[0][1:])
            end_date = parse_rm_date_to_timelinejs('D' + parts[1])
            return start_date, end_date

    elif date_type == 'S':  # From date
        start_date = parse_rm_date_to_timelinejs('D' + rm_date[1:])
        return start_date, None

    elif date_type == 'T':  # To date
        end_date = parse_rm_date_to_timelinejs('D' + rm_date[1:])
        return None, end_date

    # Standard date
    return parse_rm_date_to_timelinejs(rm_date), None
```

**Timeline Display:**
- If both start and end: Show as span on timeline
- If only start: Show as single event with "From [date]" display
- If only end: Show as single event with "Until [date]" display

---

### Rule 5: Event Text Generation

**Headline:** Event type name

**Text:** Narrative description using sentence template or generated

#### Option A: Use Sentence Template

```python
def generate_event_text_from_template(event_data, person_data):
    """Generate event text using RM sentence template."""
    # Get template from FactTypeTable.Sentence
    # Substitute variables: [person], [Date], [Place], etc.
    # See RM11_Sentence_Templates.md for details

    template = event_data['sentence_template']
    # ... template substitution logic ...
    return rendered_text
```

#### Option B: AI-Generated Narrative

```python
def generate_event_narrative(event_data, person_data, context):
    """
    Generate narrative text for event.

    Args:
        event_data: Event information (type, date, place, details)
        person_data: Person information (name, age at event)
        context: Additional context (previous events, family)

    Returns:
        str: HTML-formatted narrative paragraph
    """
    # Example for Birth event:
    name = person_data['name']
    date_str = format_date_readable(event_data['date'])
    place = event_data['place']

    text = f"<p>{name} was born"

    if date_str:
        text += f" on {date_str}"

    if place:
        place_short = format_place_short(place)  # "City, State"
        text += f" in {place_short}"

    text += ".</p>"

    # Add details if present
    if event_data['details']:
        text += f"<p>{event_data['details']}</p>"

    return text
```

**Include in Narrative:**
- Person name (first occurrence or context change)
- Event-specific details (e.g., cause of death)
- Age at event (if calculable)
- Place (formatted appropriately)
- Related context (e.g., "during World War II")

---

### Rule 6: Place Formatting

**Timeline Display:**
- Use **short form** for most events: "City, State"
- Use **medium form** for detailed events: "City, County, State"
- Omit country for domestic events (if all same country)

**Python Formatting:**
```python
def format_place_for_timeline(place_name, country_filter='United States'):
    """
    Format place for timeline display.

    Args:
        place_name: Full place hierarchy
        country_filter: Omit this country from display

    Returns:
        str: Formatted place string
    """
    if not place_name:
        return None

    levels = place_name.split(', ')

    # Remove country if matches filter
    if len(levels) >= 4 and levels[3] == country_filter:
        levels = levels[:3]

    # Return City, State (or City, Country if international)
    if len(levels) >= 3:
        return f"{levels[0]}, {levels[2]}"  # City, State
    elif len(levels) == 2:
        return f"{levels[0]}, {levels[1]}"  # City, Country
    else:
        return levels[0]  # Just city
```

---

### Rule 7: Event Grouping

**Purpose:** Organize timeline into thematic sections

**Group Definitions:**

| Group Name | FactType IDs | Age Range |
|------------|--------------|-----------|
| Early Life | 1, 3, 6, 7, 21, 24 | Birth to 18 |
| Education & Career | 21, 22, 24, 26, 500 | 18+ |
| Family Life | 300, 302, 304 | All ages |
| Military Service | 501, custom types | War years |
| Later Life | 22, 29 | 60+ |
| Migration | 15, 16, 17, 18 | All ages |
| Final Years | 2, 4, 19, 20 | Death-related |

**Python Logic:**
```python
def assign_event_group(event_type_id, person_age):
    """Assign event to timeline group."""

    if event_type_id == 1:  # Birth
        return "Early Life"

    elif event_type_id in [3, 6, 7]:  # Religious events
        if person_age and person_age < 18:
            return "Early Life"
        else:
            return "Life Events"

    elif event_type_id in [21, 24, 500]:  # Education
        return "Education & Career"

    elif event_type_id == 26:  # Occupation
        return "Education & Career"

    elif event_type_id in [300, 302, 304]:  # Marriage, Divorce
        return "Family Life"

    elif event_type_id == 501 or 'War' in event_type_name:
        return "Military Service"

    elif event_type_id in [15, 16, 17, 18, 29]:  # Migration, Census
        return "Migration & Residence"

    elif event_type_id in [2, 4, 19, 20]:  # Death, Burial, Probate
        return "Final Years"

    else:
        return "Life Events"
```

---

### Rule 8: Media Attachment

**Sources:**
1. **MultimediaTable** - Photos, documents linked to events
2. **Citation sources** - Document images from sources
3. **Generated media** - Maps, charts created from data

**Query Media for Event:**
```sql
SELECT
    m.MediaID,
    m.MediaFile,
    m.Caption,
    m.Description
FROM MediaLinkTable ml
JOIN MultimediaTable m ON ml.MediaID = m.MediaID
WHERE ml.OwnerType = 2  -- Event
  AND ml.OwnerID = ?    -- EventID
ORDER BY ml.SortOrder
LIMIT 1;  -- First media item
```

**TimelineJS3 Media Object:**
```json
{
  "url": "media/photos/john_iams_1921.jpg",
  "caption": "John Dorsey Iams as an infant",
  "credit": "Family photograph collection",
  "thumbnail": "media/thumbs/john_iams_1921_thumb.jpg"
}
```

**Supported Media Types:**
- Images: JPG, PNG, GIF
- Documents: PDF (if publicly accessible)
- Videos: YouTube, Vimeo URLs
- Maps: Location coordinates can generate map embed
- External links: URLs to online resources

---

### Rule 9: Citation as Credit

**Purpose:** Attribute information sources in timeline

**Format:**
```python
def format_citation_for_credit(event_id, conn):
    """Get citation text for media credit field."""

    cursor = conn.cursor()

    # Get first citation for event
    cursor.execute("""
        SELECT c.CitationName, s.Name as SourceName
        FROM CitationLinkTable cl
        JOIN CitationTable c ON cl.CitationID = c.CitationID
        JOIN SourceTable s ON c.SourceID = s.SourceID
        WHERE cl.OwnerType = 2
          AND cl.OwnerID = ?
        ORDER BY cl.LinkID
        LIMIT 1
    """, (event_id,))

    result = cursor.fetchone()
    if result:
        citation_name, source_name = result
        if citation_name:
            return f"{source_name}, {citation_name}"
        else:
            return source_name

    return "Family records"
```

---

### Rule 10: Handling Undated Events

**Problem:** Events without dates can't be placed chronologically

**Solutions:**

**Option 1: Exclude from Timeline**
- Only include dated events
- List undated events separately

**Option 2: Estimate Date from Context**
```python
def estimate_event_date(event, person_birth_date):
    """Estimate date for undated events based on typical ages."""

    event_type = event['type_id']
    typical_ages = {
        30: person_birth_date + 16,  # SSN (age 16)
        26: person_birth_date + 25,  # First occupation (age 25)
        300: person_birth_date + 25, # Marriage (age 25)
        4: person_death_date         # Burial (at death)
    }

    if event_type in typical_ages:
        return typical_ages[event_type]

    return None
```

**Option 3: Group at Era Level**
- Create timeline era (e.g., "1940s")
- Place undated events in relevant era

**Option 4: End of Timeline Section**
- Create special "Undated Events" section
- List events without timeline placement

---

## Complete Timeline Generation Example

### Python: Generate TimelineJS3 JSON

```python
import json
import sqlite3
from datetime import datetime

def generate_person_timeline(person_id, db_path, include_private=False):
    """
    Generate TimelineJS3 JSON timeline for a person.

    Args:
        person_id: PersonID from PersonTable
        db_path: Path to RootsMagic database
        include_private: Include private events

    Returns:
        dict: TimelineJS3 JSON structure
    """
    conn = connect_rmtree(db_path)
    cursor = conn.cursor()

    # Get person details
    cursor.execute("""
        SELECT
            n.Surname,
            n.Given,
            n.BirthYear,
            n.DeathYear
        FROM PersonTable p
        JOIN NameTable n ON p.PersonID = n.OwnerID AND n.IsPrimary = 1
        WHERE p.PersonID = ?
    """, (person_id,))

    surname, given, birth_year, death_year = cursor.fetchone()
    full_name = f"{given} {surname}"

    # Get all events
    cursor.execute("""
        SELECT
            e.EventID,
            ft.FactTypeID,
            ft.Name as EventType,
            e.Date,
            e.SortDate,
            e.Details,
            pl.Name as Place,
            e.IsPrivate,
            e.Proof
        FROM EventTable e
        JOIN FactTypeTable ft ON e.EventType = ft.FactTypeID
        LEFT JOIN PlaceTable pl ON e.PlaceID = pl.PlaceID
        WHERE e.OwnerType = 0
          AND e.OwnerID = ?
          AND e.EventType NOT IN (30, 34, 35)  -- Exclude identifiers
        ORDER BY e.SortDate
    """, (person_id,))

    events = cursor.fetchall()

    # Build timeline structure
    timeline = {
        "title": {
            "text": {
                "headline": full_name,
                "text": f"Born {birth_year}, Died {death_year}" if death_year else f"Born {birth_year}"
            }
        },
        "events": [],
        "scale": "human"
    }

    # Process each event
    for event_data in events:
        (event_id, fact_type_id, event_type, rm_date, sort_date,
         details, place, is_private, proof) = event_data

        # Skip private events unless requested
        if is_private and not include_private:
            continue

        # Skip unknown dates (for main timeline)
        if sort_date == 9223372036854775807:
            continue  # Or handle as undated

        # Parse date
        start_date, end_date = parse_date_range(rm_date)
        if not start_date:
            continue

        # Calculate age at event
        person_age = None
        if birth_year and start_date.get('year'):
            person_age = start_date['year'] - birth_year

        # Format place
        place_formatted = format_place_for_timeline(place)

        # Generate narrative text
        text_content = generate_event_narrative({
            'type': event_type,
            'date': rm_date,
            'place': place,
            'details': details,
            'age': person_age
        }, {
            'name': full_name
        })

        # Build event object
        timeline_event = {
            "start_date": start_date,
            "text": {
                "headline": event_type,
                "text": text_content
            },
            "group": assign_event_group(fact_type_id, person_age),
            "unique_id": f"event_{event_id}_{person_id}"
        }

        # Add end date if range
        if end_date:
            timeline_event["end_date"] = end_date

        # Add media if available
        media = get_event_media(event_id, conn)
        if media:
            timeline_event["media"] = media

        # Add to timeline
        timeline["events"].append(timeline_event)

    conn.close()
    return timeline

# Usage
timeline_json = generate_person_timeline(1872, 'data/Iiams.rmtree')
with open('timeline.json', 'w') as f:
    json.dump(timeline_json, f, indent=2)
```

---

## Timeline Era Definitions

**Purpose:** Provide historical context for events

**Example Eras:**

```json
{
  "eras": [
    {
      "start_date": {"year": 1914},
      "end_date": {"year": 1918},
      "text": {
        "headline": "World War I",
        "text": "The Great War"
      }
    },
    {
      "start_date": {"year": 1929},
      "end_date": {"year": 1939},
      "text": {
        "headline": "Great Depression",
        "text": "Economic crisis"
      }
    },
    {
      "start_date": {"year": 1939},
      "end_date": {"year": 1945},
      "text": {
        "headline": "World War II",
        "text": "Global conflict"
      }
    }
  ]
}
```

---

## Notes for AI Agents

1. **Privacy matters** - Respect IsPrivate flag, especially for living persons

2. **Date precision varies** - Handle missing months/days gracefully

3. **Same-date events common** - Census records multiple people on same date

4. **Group for readability** - Timelines with 50+ events need grouping

5. **Media enhances engagement** - Prioritize events with photos

6. **Citations provide credibility** - Include source attributions

7. **Context matters** - Add historical eras for multi-decade timelines

8. **Mobile-friendly** - TimelineJS3 works on mobile, keep text concise

9. **Unknown dates** - Provide separate "Undated Events" section or omit

10. **Proof levels** - Consider highlighting low-proof events differently

---

## Related Documentation

- **RM11_Schema_Reference.md** - EventTable, FactTypeTable structures
- **RM11_Date_Format.md** - Date encoding specification
- **RM11_FactTypes.md** - Event type categorization
- **RM11_Place_Format.md** - Place name formatting
- **RM11_Sentence_Templates.md** - Narrative text generation

---

## Summary

Timeline construction from RootsMagic data involves:

1. **Extract events** - Query EventTable with filters (private, dated, relevant)
2. **Parse dates** - Convert RM11 24-char format to TimelineJS3 date objects
3. **Order chronologically** - Sort by SortDate, handle same-date priority
4. **Generate narratives** - Create readable text from templates or AI
5. **Format places** - Use short form (City, State) for display
6. **Group events** - Organize into life phases (Early Life, Career, etc.)
7. **Add media** - Attach photos, documents from MultimediaTable
8. **Provide context** - Include eras, citations, background info
9. **Handle edge cases** - Undated events, date ranges, private data
10. **Export JSON** - Format for TimelineJS3 consumption

The result is an interactive, visual timeline that brings genealogical data to life.

---

**End of Document**
