"""
Integration test: Populate 1940 census for PersonID=1651 (Jesse Dorsey Iams) household.

Tests:
1. Insert pseudo census data into sidecar database
2. Query consolidated RM + sidecar data
3. Generate biography-ready narrative
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
from pathlib import Path
from datetime import datetime

# Paths
RM_DB_PATH = Path("data/Iiams.rmtree")
CENSUS_DB_URL = "postgresql://rmagent:census_dev_password@localhost:5432/census_sidecar"

# Household data for 1940 census
HOUSEHOLD_DATA = {
    "event_id": 16094,
    "media_id": 331,
    "census_year": 1940,
    "image_path": "?\\Records - Census\\1940 Federal/1940, Oklahoma, Tulsa - Iams, Jesse Dorsey.jpg",
    "dwelling_number": "123",
    "family_number": "123",
    "address": "1234 Main St, Tulsa, Oklahoma",
    "enumeration_district": "72-85",
    "sheet_number": "5A",
    "line_number_start": 25,
    "line_number_end": 31,
}

# Person entries
PERSONS = [
    {
        "person_id": 1651,
        "event_id": 16094,
        "citation_id": 5480,  # Placeholder
        "line_number": 25,
        "name": "Jesse Dorsey Iams",
        "age": 56,  # 1940 - 1884
        "sex": "M",
        "race": "White",
        "birthplace": "Indian Territory",
        "occupation": "Oil field superintendent",
        "fields": {
            "relationship_to_head": "Head",
            "marital_status": "Married",
            "education_level": "High school, 4 years",
            "employment_status": "At work",
            "hours_worked": "48",
            "income_wages": "3500",
            "residence_1935": "Same house",
            "birthplace_father": "Pennsylvania",
            "birthplace_mother": "Pennsylvania",
        }
    },
    {
        "person_id": 1762,
        "event_id": 16094,
        "citation_id": 5480,
        "line_number": 26,
        "name": "Margaret Shannon Iams",
        "age": 45,  # 1940 - 1895
        "sex": "F",
        "race": "White",
        "birthplace": "New York",
        "occupation": "None",
        "fields": {
            "relationship_to_head": "Wife",
            "marital_status": "Married",
            "education_level": "High school, 4 years",
            "employment_status": "None",
            "hours_worked": "0",
            "income_wages": "0",
            "residence_1935": "Same house",
            "birthplace_father": "New York",
            "birthplace_mother": "New York",
        }
    },
    {
        "person_id": 1541,
        "event_id": 16094,
        "citation_id": 5480,
        "line_number": 27,
        "name": "Donald Richard Iams",
        "age": 24,  # 1940 - 1916
        "sex": "M",
        "race": "White",
        "birthplace": "Oklahoma",
        "occupation": "Clerk, oil company",
        "fields": {
            "relationship_to_head": "Son",
            "marital_status": "Single",
            "education_level": "College, 2 years",
            "employment_status": "At work",
            "hours_worked": "44",
            "income_wages": "1800",
            "residence_1935": "Same house",
            "birthplace_father": "Indian Territory",
            "birthplace_mother": "New York",
        }
    },
    {
        "person_id": 1872,
        "event_id": 16094,
        "citation_id": 5480,
        "line_number": 28,
        "name": "John Dorsey Iams",
        "age": 19,  # 1940 - 1921
        "sex": "M",
        "race": "White",
        "birthplace": "Oklahoma",
        "occupation": "Student",
        "fields": {
            "relationship_to_head": "Son",
            "marital_status": "Single",
            "education_level": "College, 1 year",
            "employment_status": "In school",
            "hours_worked": "0",
            "income_wages": "0",
            "residence_1935": "Same house",
            "birthplace_father": "Indian Territory",
            "birthplace_mother": "New York",
        }
    },
    {
        "person_id": 1981,
        "event_id": 16094,
        "citation_id": 5480,
        "line_number": 29,
        "name": "Kathrine Virginia Iams",
        "age": 16,  # 1940 - 1924
        "sex": "F",
        "race": "White",
        "birthplace": "Oklahoma",
        "occupation": "None",
        "fields": {
            "relationship_to_head": "Daughter",
            "marital_status": "Single",
            "education_level": "High school, 2 years",
            "employment_status": "In school",
            "hours_worked": "0",
            "income_wages": "0",
            "residence_1935": "Same house",
            "birthplace_father": "Indian Territory",
            "birthplace_mother": "New York",
        }
    },
    {
        "person_id": 445,
        "event_id": 16094,
        "citation_id": 5480,
        "line_number": 30,
        "name": "Sarah Kathrine Shannon",
        "age": 83,  # 1940 - 1857
        "sex": "F",
        "race": "White",
        "birthplace": "New York",
        "occupation": "None",
        "fields": {
            "relationship_to_head": "Mother-in-law",
            "marital_status": "Widowed",
            "education_level": "Elementary school, 8 years",
            "employment_status": "None",
            "hours_worked": "0",
            "income_wages": "0",
            "residence_1935": "Same house",
            "birthplace_father": "New York",
            "birthplace_mother": "New York",
        }
    },
    {
        "person_id": 0,  # Unnamed person in RM (WitnessTable has PersonID=0)
        "event_id": 16094,
        "citation_id": 5480,
        "line_number": 31,
        "name": "Mary Johnson",  # Name from OCR, not in RM
        "age": 45,
        "sex": "F",
        "race": "Black",
        "birthplace": "Oklahoma",
        "occupation": "Domestic servant",
        "fields": {
            "relationship_to_head": "Servant",
            "marital_status": "Married",
            "education_level": "Elementary school, 5 years",
            "employment_status": "At work",
            "hours_worked": "48",
            "income_wages": "400",
            "residence_1935": "Different house, same city",
            "birthplace_father": "Texas",
            "birthplace_mother": "Texas",
        }
    },
]


def populate_census_data():
    """Populate sidecar database with 1940 census data."""

    print("="*80)
    print("POPULATING 1940 CENSUS DATA FOR JESSE DORSEY IAMS HOUSEHOLD")
    print("="*80)
    print()

    # Connect to sidecar database
    conn = psycopg2.connect(CENSUS_DB_URL)
    cur = conn.cursor()

    try:
        # Step 1: Insert census_page
        print("1. Inserting census_page record...")
        cur.execute("""
            INSERT INTO census_page (media_id, person_id, census_year, image_path)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (media_id) DO UPDATE SET
                person_id = EXCLUDED.person_id,
                census_year = EXCLUDED.census_year,
                image_path = EXCLUDED.image_path
            RETURNING page_id
        """, (HOUSEHOLD_DATA["media_id"], 1651, HOUSEHOLD_DATA["census_year"],
              HOUSEHOLD_DATA["image_path"]))

        page_id = cur.fetchone()[0]
        print(f"   ✅ Created census_page with page_id={page_id}")

        # Step 2: Insert census_household
        print("\n2. Inserting census_household record...")
        cur.execute("""
            INSERT INTO census_household
            (page_id, dwelling_number, family_number, address, enumeration_district,
             sheet_number, line_number_start, line_number_end)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING household_id
        """, (page_id, HOUSEHOLD_DATA["dwelling_number"], HOUSEHOLD_DATA["family_number"],
              HOUSEHOLD_DATA["address"], HOUSEHOLD_DATA["enumeration_district"],
              HOUSEHOLD_DATA["sheet_number"], HOUSEHOLD_DATA["line_number_start"],
              HOUSEHOLD_DATA["line_number_end"]))

        household_id = cur.fetchone()[0]
        print(f"   ✅ Created census_household with household_id={household_id}")
        print(f"      Address: {HOUSEHOLD_DATA['address']}")
        print(f"      Dwelling: {HOUSEHOLD_DATA['dwelling_number']}, Family: {HOUSEHOLD_DATA['family_number']}")
        print(f"      Lines: {HOUSEHOLD_DATA['line_number_start']}-{HOUSEHOLD_DATA['line_number_end']}")

        # Step 3: Insert census_entry records
        print(f"\n3. Inserting {len(PERSONS)} census_entry records...")
        entry_ids = []

        for person in PERSONS:
            cur.execute("""
                INSERT INTO census_entry
                (household_id, person_id, event_id, citation_id, line_number,
                 census_format, implied, name, age, sex, race, birthplace, occupation,
                 fields, review_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING entry_id
            """, (household_id, person['person_id'], person['event_id'], person['citation_id'],
                  person['line_number'], 'individual', False, person['name'], person['age'],
                  person['sex'], person['race'], person['birthplace'], person['occupation'],
                  psycopg2.extras.Json(person['fields']), 'pending'))

            entry_id = cur.fetchone()[0]
            entry_ids.append(entry_id)

            if person['person_id'] is None:
                person_label = "No PersonID"
            elif person['person_id'] == 0:
                person_label = "PersonID=0 (unnamed in RM)"
            else:
                person_label = f"PersonID={person['person_id']}"
            print(f"   ✅ Line {person['line_number']}: {person['name']} ({person_label})")
            print(f"      {person['age']} years old, {person['fields']['relationship_to_head']}, {person['occupation']}")

        # Step 4: Insert mock provenance records for name field
        print(f"\n4. Inserting provenance records for name fields...")
        for i, entry_id in enumerate(entry_ids):
            cur.execute("""
                INSERT INTO census_field_provenance
                (entry_id, field_path, ocr_model, ocr_confidence, raw_ocr_text)
                VALUES (%s, %s, %s, %s, %s)
            """, (entry_id, 'name', 'tesseract', 0.95, PERSONS[i]['name']))

        print(f"   ✅ Created {len(entry_ids)} provenance records")

        # Commit all changes
        conn.commit()

        print("\n" + "="*80)
        print("✅ CENSUS DATA POPULATION COMPLETE!")
        print("="*80)
        print(f"\nSummary:")
        print(f"  Page ID: {page_id}")
        print(f"  Household ID: {household_id}")
        print(f"  Entry IDs: {', '.join(map(str, entry_ids))}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def query_consolidated_data():
    """Query consolidated RM + sidecar data for biography generation."""

    print("\n\n" + "="*80)
    print("CONSOLIDATED RM + SIDECAR QUERY (Biography-Ready)")
    print("="*80)
    print()

    # Connect to both databases
    rm_conn = sqlite3.connect(str(RM_DB_PATH))
    rm_conn.row_factory = sqlite3.Row

    # Load ICU extension for RMNOCASE collation
    try:
        rm_conn.enable_load_extension(True)
        rm_conn.load_extension("./sqlite-extension/icu.dylib")
        rm_conn.execute(
            "SELECT icu_load_collation('en_US@colStrength=primary;caseLevel=off;normalization=on','RMNOCASE')"
        )
        rm_conn.enable_load_extension(False)
    except Exception as e:
        print(f"⚠️  Warning: Could not load ICU extension: {e}")

    sidecar_conn = psycopg2.connect(CENSUS_DB_URL)
    sidecar_cur = sidecar_conn.cursor()

    try:
        # Get RootsMagic person data
        print("Fetching RootsMagic data for household members...")
        rm_cur = rm_conn.cursor()

        # Only query for valid PersonIDs (exclude None and 0)
        person_ids = [p['person_id'] for p in PERSONS if p['person_id'] and p['person_id'] > 0]
        placeholders = ','.join('?' * len(person_ids))

        rm_cur.execute(f"""
            SELECT
                p.PersonID,
                n.Given,
                n.Surname,
                n.Prefix,
                n.Suffix,
                p.Sex,
                birth.Date as BirthDate,
                birth.PlaceName as BirthPlace,
                death.Date as DeathDate,
                death.PlaceName as DeathPlace
            FROM PersonTable p
            JOIN NameTable n ON n.OwnerID = p.PersonID AND n.IsPrimary = 1
            LEFT JOIN (
                SELECT e.OwnerID, e.Date, pl.Name as PlaceName
                FROM EventTable e
                JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'BIRT'
                LEFT JOIN PlaceTable pl ON pl.PlaceID = e.PlaceID
            ) birth ON birth.OwnerID = p.PersonID
            LEFT JOIN (
                SELECT e.OwnerID, e.Date, pl.Name as PlaceName
                FROM EventTable e
                JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'DEAT'
                LEFT JOIN PlaceTable pl ON pl.PlaceID = e.PlaceID
            ) death ON death.OwnerID = p.PersonID
            WHERE p.PersonID IN ({placeholders})
        """, person_ids)

        rm_data = {row['PersonID']: dict(row) for row in rm_cur.fetchall()}
        print(f"   ✅ Retrieved data for {len(rm_data)} persons from RootsMagic")

        # Get sidecar census data
        print("\nFetching census data from sidecar database...")
        # Query includes valid PersonIDs, plus PersonID=0 and NULL entries
        all_person_ids = person_ids + [0] if 0 not in person_ids else person_ids
        sidecar_cur.execute("""
            SELECT
                ce.entry_id,
                ce.person_id,
                ce.line_number,
                ce.name,
                ce.age,
                ce.sex,
                ce.race,
                ce.birthplace,
                ce.occupation,
                ce.fields,
                ch.address,
                ch.dwelling_number,
                ch.family_number,
                ch.sheet_number,
                cp.census_year
            FROM census_entry ce
            JOIN census_household ch ON ce.household_id = ch.household_id
            JOIN census_page cp ON ch.page_id = cp.page_id
            WHERE ce.person_id = ANY(%s) OR ce.person_id IS NULL OR ce.person_id = 0
            ORDER BY ce.line_number
        """, (all_person_ids,))

        census_data = sidecar_cur.fetchall()
        print(f"   ✅ Retrieved {len(census_data)} census entries from sidecar")

        # Generate consolidated report
        print("\n\n" + "="*80)
        print("CONSOLIDATED HOUSEHOLD REPORT")
        print("="*80)
        print()

        # Household header
        first_entry = census_data[0]
        print(f"📍 Address: {first_entry[10]}")
        print(f"📅 Census Year: {first_entry[14]}")
        print(f"🏠 Dwelling: {first_entry[11]}, Family: {first_entry[12]}, Sheet: {first_entry[13]}")
        print()

        # Person entries
        for entry in census_data:
            entry_id, person_id, line_num, name, age, sex, race, birthplace, occupation, fields, *_ = entry

            print(f"Line {line_num}: {name}")
            print(f"{'─' * 80}")

            # RootsMagic data (if available)
            if person_id is None:
                print(f"  ⚠️  Not in RootsMagic database (discovered via OCR only)")
            elif person_id == 0:
                print(f"  ⚠️  PersonID=0: Unnamed person in RootsMagic")
                print(f"     (Linked to event as '{name}' role, but no PersonTable record)")
                print(f"     OCR extracted name: {name}")
            elif person_id in rm_data:
                rm_person = rm_data[person_id]
                print(f"  📇 RootsMagic PersonID: {person_id}")
                print(f"  👤 Full Name: {rm_person['Prefix'] or ''} {rm_person['Given']} {rm_person['Surname']} {rm_person['Suffix'] or ''}".strip())
                print(f"  🎂 Birth: {rm_person['BirthDate']} in {rm_person['BirthPlace']}")
                if rm_person['DeathDate']:
                    print(f"  ⚰️  Death: {rm_person['DeathDate']} in {rm_person['DeathPlace']}")
            else:
                print(f"  ⚠️  PersonID={person_id} not found in RootsMagic data")

            print()

            # Census data
            print(f"  Census Information:")
            print(f"    Age: {age} years old")
            print(f"    Sex: {sex}, Race: {race}")
            print(f"    Birthplace: {birthplace}")
            print(f"    Occupation: {occupation}")

            # JSONB fields
            if fields:
                fields_dict = json.loads(fields) if isinstance(fields, str) else fields
                print(f"    Relationship: {fields_dict.get('relationship_to_head')}")
                print(f"    Marital Status: {fields_dict.get('marital_status')}")
                print(f"    Education: {fields_dict.get('education_level')}")
                print(f"    Employment: {fields_dict.get('employment_status')}")
                if fields_dict.get('income_wages') and int(fields_dict['income_wages']) > 0:
                    print(f"    Income: ${fields_dict['income_wages']}")
                print(f"    1935 Residence: {fields_dict.get('residence_1935')}")

            print()

        # Generate biography narrative
        print("\n\n" + "="*80)
        print("BIOGRAPHY NARRATIVE GENERATION")
        print("="*80)
        print()

        head_entry = census_data[0]
        head_id = head_entry[1]
        head_rm = rm_data.get(head_id) if head_id else None
        head_name = f"{head_rm['Given']} {head_rm['Surname']}" if head_rm else head_entry[3]
        head_fields = json.loads(head_entry[9]) if isinstance(head_entry[9], str) else head_entry[9]

        narrative = f"""
In the {head_entry[14]} census, {head_name} was enumerated at {head_entry[10]} in Tulsa, Oklahoma. """

        narrative += f"At age {head_entry[4]}, {head_name} was working as {head_entry[8].lower()}, "
        narrative += f"earning ${head_fields['income_wages']} annually. "

        # Household composition
        household_members = []
        for entry in census_data[1:]:
            fields = json.loads(entry[9]) if isinstance(entry[9], str) else entry[9]
            rel = fields.get('relationship_to_head', 'member').lower()
            household_members.append(f"{entry[3]} ({rel}, age {entry[4]})")

        if household_members:
            narrative += f"The household included {', '.join(household_members)}. "

        narrative += f"The family had been living at the same residence since 1935."

        print("Generated Narrative:")
        print("─" * 80)
        print(narrative)
        print()

    finally:
        rm_conn.close()
        sidecar_conn.close()


if __name__ == "__main__":
    print("\n🧪 INTEGRATION TEST: 1940 Census for Jesse Dorsey Iams Household\n")

    # Step 1: Populate census data
    populate_census_data()

    # Step 2: Query and generate narrative
    query_consolidated_data()

    print("\n✅ Integration test complete!\n")
