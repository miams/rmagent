"""
Test script for census catalog query.

Tests the catalog query on actual RootsMagic database to verify:
1. Which MediaIDs contain census images
2. Which PersonIDs are linked to each image
3. EventIDs and CitationIDs for each person
4. Census year extraction from event date
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

# Path to RootsMagic database
RM_DB_PATH = Path("data/Iiams.rmtree")


def test_catalog_query():
    """Test the enhanced catalog query."""

    conn = sqlite3.connect(str(RM_DB_PATH))
    conn.row_factory = sqlite3.Row

    # Enhanced catalog query with 4 pathways for both pre-1850 and post-1850
    query = """
    -- Pathway 1: Media → Event (Post-1850 typical) - Primary person
    SELECT
        m.MediaID,
        m.MediaPath,
        m.MediaFile,
        e.EventID,
        e.OwnerID as PersonID,
        e.Date as EventDate,
        c.CitationID,
        c.CitationName,
        n.Surname,
        n.Given,
        p.Sex,
        'Head' as Role,
        NULL as RoleID,
        'Media→Event' as LinkPath,
        NULL as census_year
    FROM MultimediaTable m
    JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 2
    JOIN EventTable e ON e.EventID = ml.OwnerID
    JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
    LEFT JOIN CitationLinkTable cl ON cl.OwnerID = e.EventID AND cl.OwnerType = 2
    LEFT JOIN CitationTable c ON c.CitationID = cl.CitationID
    LEFT JOIN PersonTable p ON p.PersonID = e.OwnerID
    LEFT JOIN NameTable n ON n.OwnerID = e.OwnerID AND n.IsPrimary = 1
    WHERE m.MediaType = 1

    UNION ALL

    -- Pathway 2: Media → Event (Post-1850 typical) - Witnesses/household members
    SELECT
        m.MediaID,
        m.MediaPath,
        m.MediaFile,
        e.EventID,
        w.PersonID,
        e.Date as EventDate,
        c.CitationID,
        c.CitationName,
        n.Surname,
        n.Given,
        p.Sex,
        r.RoleName as Role,
        w.Role as RoleID,
        'Media→Event+Witness' as LinkPath,
        NULL as census_year
    FROM MultimediaTable m
    JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 2
    JOIN EventTable e ON e.EventID = ml.OwnerID
    JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
    JOIN WitnessTable w ON w.EventID = e.EventID
    LEFT JOIN RoleTable r ON r.RoleID = w.Role
    LEFT JOIN CitationLinkTable cl ON cl.OwnerID = e.EventID AND cl.OwnerType = 2
    LEFT JOIN CitationTable c ON c.CitationID = cl.CitationID
    LEFT JOIN PersonTable p ON p.PersonID = w.PersonID
    LEFT JOIN NameTable n ON n.OwnerID = w.PersonID AND n.IsPrimary = 1
    WHERE m.MediaType = 1

    UNION ALL

    -- Pathway 3: Media → Citation → Event (Pre-1850 typical)
    SELECT
        m.MediaID,
        m.MediaPath,
        m.MediaFile,
        e.EventID,
        e.OwnerID as PersonID,
        e.Date as EventDate,
        c.CitationID,
        c.CitationName,
        n.Surname,
        n.Given,
        p.Sex,
        'Head' as Role,
        NULL as RoleID,
        'Media→Citation→Event' as LinkPath,
        NULL as census_year
    FROM MultimediaTable m
    JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 4
    JOIN CitationTable c ON c.CitationID = ml.OwnerID
    JOIN CitationLinkTable cl ON cl.CitationID = c.CitationID AND cl.OwnerType = 2
    JOIN EventTable e ON e.EventID = cl.OwnerID
    JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
    LEFT JOIN PersonTable p ON p.PersonID = e.OwnerID
    LEFT JOIN NameTable n ON n.OwnerID = e.OwnerID AND n.IsPrimary = 1
    WHERE m.MediaType = 1

    UNION ALL

    -- Pathway 4: Media → Source → Citation → Event (Pre-1850 typical)
    SELECT
        m.MediaID,
        m.MediaPath,
        m.MediaFile,
        e.EventID,
        e.OwnerID as PersonID,
        e.Date as EventDate,
        c.CitationID,
        c.CitationName,
        n.Surname,
        n.Given,
        p.Sex,
        'Head' as Role,
        NULL as RoleID,
        'Media→Source→Citation→Event' as LinkPath,
        NULL as census_year
    FROM MultimediaTable m
    JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 3
    JOIN SourceTable s ON s.SourceID = ml.OwnerID
    JOIN CitationTable c ON c.SourceID = s.SourceID
    JOIN CitationLinkTable cl ON cl.CitationID = c.CitationID AND cl.OwnerType = 2
    JOIN EventTable e ON e.EventID = cl.OwnerID
    JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
    LEFT JOIN PersonTable p ON p.PersonID = e.OwnerID
    LEFT JOIN NameTable n ON n.OwnerID = e.OwnerID AND n.IsPrimary = 1
    WHERE m.MediaType = 1

    ORDER BY census_year DESC, MediaPath, EventID, PersonID
    """

    results = conn.execute(query).fetchall()

    # Extract census year from path in Python
    import re
    results_with_year = []
    for row in results:
        row_dict = dict(row)
        # Extract 4-digit year from path (1790-1959)
        match = re.search(r'\b(1[78]\d{2}|19[0-5]\d)\b', row_dict['MediaPath'])
        row_dict['census_year'] = int(match.group(1)) if match else None
        results_with_year.append(row_dict)

    results = results_with_year

    print(f"\n{'='*80}")
    print(f"CENSUS CATALOG QUERY RESULTS")
    print(f"{'='*80}\n")

    if not results:
        print("❌ No census events with media found!")
        return

    print(f"✅ Found {len(results)} person-media links\n")

    # Group by MediaID
    by_media = defaultdict(list)
    for row in results:
        by_media[row['MediaID']].append(dict(row))

    print(f"📊 Summary:")
    print(f"   - Total images with census data: {len(by_media)}")
    print(f"   - Total person-image links: {len(results)}")
    print(f"   - Average persons per image: {len(results) / len(by_media):.1f}\n")

    # Statistics by linkage pathway
    by_pathway = defaultdict(int)
    for row in results:
        by_pathway[row['LinkPath']] += 1

    print(f"📊 Linkage Pathways:")
    for pathway in sorted(by_pathway.keys(), key=lambda x: -by_pathway[x]):
        count = by_pathway[pathway]
        pct = count / len(results) * 100
        print(f"   {pathway}: {count} links ({pct:.1f}%)")
    print()

    # Pre-1850 specific statistics
    pre_1850 = [r for r in results if r['census_year'] and r['census_year'] < 1850]
    if pre_1850:
        print(f"🎯 Pre-1850 Census:")
        print(f"   Total person-media links: {len(pre_1850)}")
        pre_1850_years = defaultdict(int)
        for r in pre_1850:
            pre_1850_years[r['census_year']] += 1
        for year in sorted(pre_1850_years.keys()):
            print(f"   {year}: {pre_1850_years[year]} links")
        print()

    # Show first 5 images with details
    print(f"\n{'='*80}")
    print(f"FIRST 5 IMAGES (Detailed)")
    print(f"{'='*80}\n")

    for idx, (media_id, persons) in enumerate(list(by_media.items())[:5], 1):
        first_person = persons[0]

        print(f"{idx}. MediaID: {media_id}")
        print(f"   Path: {first_person['MediaPath']}/{first_person['MediaFile']}")
        print(f"   Census Year: {first_person['census_year']}")
        print(f"   Persons on this image: {len(persons)}")
        print()

        for person in persons:
            citation_info = f"CitationID={person['CitationID']}" if person['CitationID'] else "No Citation"
            role_info = f" ({person['Role']})" if person['Role'] else ""
            print(f"      • PersonID={person['PersonID']}: {person['Given']} {person['Surname']}{role_info}")
            print(f"        EventID={person['EventID']}, {citation_info}")
            print(f"        Sex={person['Sex']}")
            print()

    # Statistics by census year
    print(f"\n{'='*80}")
    print(f"STATISTICS BY CENSUS YEAR")
    print(f"{'='*80}\n")

    by_year = defaultdict(lambda: {'images': set(), 'persons': 0})
    for row in results:
        year = row['census_year']
        if year:
            by_year[year]['images'].add(row['MediaID'])
            by_year[year]['persons'] += 1

    for year in sorted(by_year.keys(), reverse=True):
        stats = by_year[year]
        print(f"   {year}: {len(stats['images'])} images, {stats['persons']} persons")

    # Check for missing data
    print(f"\n{'='*80}")
    print(f"DATA QUALITY CHECKS")
    print(f"{'='*80}\n")

    missing_citation = sum(1 for r in results if not r['CitationID'])
    missing_year = sum(1 for r in results if not r['census_year'])

    if missing_citation > 0:
        print(f"   ⚠️  {missing_citation} events missing CitationID ({missing_citation/len(results)*100:.1f}%)")
    else:
        print(f"   ✅ All events have CitationID")

    if missing_year > 0:
        print(f"   ⚠️  {missing_year} events missing census_year ({missing_year/len(results)*100:.1f}%)")
    else:
        print(f"   ✅ All events have census_year")


    # Show any events without citations
    if missing_citation > 0:
        print(f"\n   Events without citations:")
        for row in results[:5]:  # Show first 5
            if not row['CitationID']:
                print(f"      EventID={row['EventID']}, PersonID={row['PersonID']} ({row['Given']} {row['Surname']})")

    conn.close()

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    test_catalog_query()
