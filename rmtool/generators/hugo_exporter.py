"""
Hugo blog post exporter for RMTool.

Generates Hugo-compatible Markdown files with YAML front matter for creating
static site biographies. Integrates biography content, timelines, media, and
proper Hugo taxonomies.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from rmtool.generators.biography import BiographyGenerator, BiographyLength, CitationStyle
from rmtool.generators.timeline import TimelineGenerator, TimelineFormat
from rmtool.rmlib.database import RMDatabase
from rmtool.rmlib.models import OwnerType
from rmtool.rmlib.parsers.name_parser import format_full_name
from rmtool.rmlib.queries import QueryService


def _get_row_value(row, key: str, default=None):
    """Get value from sqlite3.Row object with default."""
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, TypeError):
        return default


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


class HugoExporter:
    """
    Export RootsMagic data as Hugo-compatible blog posts.

    Creates Hugo markdown files with YAML front matter, embedded biography
    content, timeline integration, and proper taxonomies (categories, tags).

    Args:
        db: RMDatabase instance or path to database
        extension_path: Path to ICU extension (default: ./sqlite-extension/icu.dylib)
        media_base_path: Base path for media in Hugo (default: /media/)

    Example:
        ```python
        from rmtool.generators.hugo_exporter import HugoExporter

        exporter = HugoExporter(db="data/Iiams.rmtree")

        # Export single person
        exporter.export_person(
            person_id=1,
            output_dir="hugo-site/content/people"
        )

        # Export multiple people
        exporter.export_batch(
            person_ids=[1, 2, 3],
            output_dir="hugo-site/content/people"
        )
        ```
    """

    def __init__(
        self,
        db: Optional[RMDatabase | Path | str] = None,
        extension_path: Path | str = Path("./sqlite-extension/icu.dylib"),
        media_base_path: str = "/media/",
    ):
        # Handle db parameter
        if isinstance(db, (Path, str)):
            self.db_path = Path(db)
            self._db = None
            self._owns_db = True
        elif isinstance(db, RMDatabase):
            self.db_path = None
            self._db = db
            self._owns_db = False
        else:
            self.db_path = None
            self._db = None
            self._owns_db = False

        self.extension_path = Path(extension_path)
        self.media_base_path = media_base_path.rstrip('/') + '/'

    def export_person(
        self,
        person_id: int,
        output_dir: Path | str,
        bio_length: BiographyLength = BiographyLength.STANDARD,
        include_timeline: bool = True,
        include_media: bool = True,
    ) -> Dict[str, Path]:
        """
        Export a single person as Hugo blog post.

        Args:
            person_id: PersonID from PersonTable
            output_dir: Directory for content files (e.g., hugo-site/content/people)
            bio_length: Biography length
            include_timeline: Include timeline shortcode and files
            include_media: Include media references

        Returns:
            Dict with paths to created files: {'markdown': Path, 'timeline_html': Path, 'timeline_json': Path}

        Raises:
            ValueError: If person not found or no database provided
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Extract person data
        person_data = self._extract_person_data(person_id, include_media)

        # Generate biography
        biography = self._generate_biography(person_id, bio_length)

        # Generate Hugo markdown
        markdown_content = self._build_hugo_markdown(
            person_data=person_data,
            biography=biography,
            include_timeline=include_timeline,
        )

        # Create slug for filename
        slug = _slugify(person_data['full_name'])
        markdown_file = output_path / f"{slug}.md"
        markdown_file.write_text(markdown_content, encoding='utf-8')

        result = {'markdown': markdown_file}

        # Generate timeline files if requested
        if include_timeline:
            timeline_files = self._generate_timeline_files(
                person_id=person_id,
                slug=slug,
                output_dir=output_path,
            )
            result.update(timeline_files)

        return result

    def export_batch(
        self,
        person_ids: List[int],
        output_dir: Path | str,
        bio_length: BiographyLength = BiographyLength.STANDARD,
        include_timeline: bool = True,
        generate_index: bool = True,
    ) -> Dict[str, List[Path]]:
        """
        Export multiple people as Hugo blog posts.

        Args:
            person_ids: List of PersonIDs to export
            output_dir: Directory for content files
            bio_length: Biography length
            include_timeline: Include timeline files
            generate_index: Generate _index.md listing all people

        Returns:
            Dict with 'markdown_files', 'timeline_files', 'index_file' lists
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        markdown_files = []
        timeline_files = []

        for person_id in person_ids:
            try:
                result = self.export_person(
                    person_id=person_id,
                    output_dir=output_path,
                    bio_length=bio_length,
                    include_timeline=include_timeline,
                )
                markdown_files.append(result['markdown'])
                if 'timeline_html' in result:
                    timeline_files.append(result['timeline_html'])
                if 'timeline_json' in result:
                    timeline_files.append(result['timeline_json'])
            except Exception as e:
                # Continue with other people if one fails
                print(f"Warning: Failed to export person {person_id}: {e}")
                continue

        result_dict = {
            'markdown_files': markdown_files,
            'timeline_files': timeline_files,
        }

        # Generate index page
        if generate_index and markdown_files:
            index_file = self._generate_index_page(
                person_ids=person_ids,
                output_dir=output_path,
            )
            result_dict['index_file'] = index_file

        return result_dict

    def _extract_person_data(self, person_id: int, include_media: bool) -> Dict:
        """Extract person data from database."""

        def _extract(db: RMDatabase) -> Dict:
            query = QueryService(db)

            # Get person
            person = query.get_person_with_primary_name(person_id)
            if not person:
                raise ValueError(f"Person {person_id} not found")

            # Get person name
            full_name = format_full_name(
                given=_get_row_value(person, "Given"),
                surname=_get_row_value(person, "Surname"),
                prefix=_get_row_value(person, "Prefix"),
                suffix=_get_row_value(person, "Suffix"),
            )

            surname = _get_row_value(person, "Surname", "Unknown")
            birth_year = _get_row_value(person, "BirthYear")
            death_year = _get_row_value(person, "DeathYear")

            # Get places for tags
            places = self._get_person_places(db, person_id)

            # Get media if requested
            media_items = []
            if include_media:
                media_items = self._get_person_media(db, person_id)

            return {
                "person_id": person_id,
                "full_name": full_name,
                "surname": surname,
                "birth_year": birth_year,
                "death_year": death_year,
                "places": places,
                "media_items": media_items,
            }

        if self._db:
            return _extract(self._db)
        elif self.db_path:
            with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
                return _extract(db)
        else:
            raise ValueError("No database provided")

    def _generate_biography(self, person_id: int, length: BiographyLength) -> str:
        """Generate biography content."""
        bio_generator = BiographyGenerator(
            db=self.db_path or self._db,
            extension_path=self.extension_path,
        )

        biography = bio_generator.generate(
            person_id=person_id,
            length=length,
            citation_style=CitationStyle.FOOTNOTE,
            use_ai=False,  # Use template-based for consistency
        )

        return biography.render_markdown()

    def _generate_timeline_files(
        self,
        person_id: int,
        slug: str,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Generate timeline HTML and JSON files."""
        timeline_generator = TimelineGenerator(
            db=self.db_path or self._db,
            extension_path=self.extension_path,
        )

        # Create timelines subdirectory
        timelines_dir = output_dir.parent.parent / "static" / "timelines"
        timelines_dir.mkdir(parents=True, exist_ok=True)

        # Generate JSON
        json_file = timelines_dir / f"{slug}.json"
        timeline_generator.generate(
            person_id=person_id,
            format=TimelineFormat.JSON,
            output_path=json_file,
        )

        # Generate HTML viewer
        html_file = timelines_dir / f"{slug}.html"
        timeline_generator.generate(
            person_id=person_id,
            format=TimelineFormat.HTML,
            output_path=html_file,
        )

        return {
            'timeline_json': json_file,
            'timeline_html': html_file,
        }

    def _build_hugo_markdown(
        self,
        person_data: Dict,
        biography: str,
        include_timeline: bool,
    ) -> str:
        """Build complete Hugo markdown file."""
        lines = []

        # YAML front matter
        lines.append("---")
        lines.append(f"title: \"{person_data['full_name']}\"")
        lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")

        # Categories (surname)
        lines.append(f"categories: [\"{person_data['surname']} Family\"]")

        # Tags (places, time periods)
        tags = []
        if person_data['places']:
            tags.extend(person_data['places'][:5])  # Limit to 5 places
        if person_data['birth_year']:
            decade = (person_data['birth_year'] // 10) * 10
            tags.append(f"{decade}s")
        if tags:
            tag_str = ", ".join([f'"{tag}"' for tag in tags])
            lines.append(f"tags: [{tag_str}]")

        # Custom fields
        lines.append(f"person_id: {person_data['person_id']}")
        if person_data['birth_year']:
            lines.append(f"birth_year: {person_data['birth_year']}")
        if person_data['death_year']:
            lines.append(f"death_year: {person_data['death_year']}")

        lines.append("---")
        lines.append("")

        # Biography content
        # Remove the H1 title from biography (Hugo will add it)
        bio_content = biography
        bio_content = re.sub(r'^#\s+.*$', '', bio_content, count=1, flags=re.MULTILINE)
        bio_content = bio_content.strip()

        lines.append(bio_content)
        lines.append("")

        # Timeline shortcode (if requested)
        if include_timeline:
            lines.append("## Timeline")
            lines.append("")
            slug = _slugify(person_data['full_name'])
            lines.append(f'{{{{< timeline src="/timelines/{slug}.json" >}}}}')
            lines.append("")
            lines.append(f"*View [interactive timeline](/timelines/{slug}.html) in new window.*")
            lines.append("")

        # Media gallery (if available)
        if person_data['media_items']:
            lines.append("## Photos & Documents")
            lines.append("")
            for media in person_data['media_items'][:10]:  # Limit to 10 items
                media_url = self._format_media_url(media)
                caption = media.get('caption', '')
                lines.append(f"![{caption}]({media_url})")
                if caption:
                    lines.append(f"*{caption}*")
                lines.append("")

        return "\n".join(lines)

    def _get_person_places(self, db: RMDatabase, person_id: int) -> List[str]:
        """Get unique places associated with person for tags."""
        cursor = db.execute(
            """
            SELECT DISTINCT pl.Name
            FROM EventTable e
            JOIN PlaceTable pl ON e.PlaceID = pl.PlaceID
            WHERE e.OwnerType = ? AND e.OwnerID = ?
              AND pl.Name IS NOT NULL AND pl.Name != ''
            LIMIT 10
            """,
            (OwnerType.PERSON.value, person_id),
        )

        places = []
        for row in cursor.fetchall():
            place_name = _get_row_value(row, "Name")
            if place_name:
                # Extract just the city or state (first level)
                parts = place_name.split(',')
                if len(parts) >= 2:
                    # Use state/country (second-to-last part)
                    place = parts[-2].strip()
                else:
                    place = parts[0].strip()
                if place and place not in places:
                    places.append(place)

        return places

    def _get_person_media(self, db: RMDatabase, person_id: int) -> List[Dict]:
        """Get media items for person."""
        cursor = db.execute(
            """
            SELECT m.MediaID, m.MediaPath, m.MediaFile, m.Caption, m.Description
            FROM MediaLinkTable ml
            JOIN MultimediaTable m ON ml.MediaID = m.MediaID
            WHERE ml.OwnerType = ? AND ml.OwnerID = ?
            ORDER BY ml.IsPrimary DESC, ml.SortOrder
            """,
            (OwnerType.PERSON.value, person_id),
        )

        media_items = []
        for row in cursor.fetchall():
            media_items.append({
                'media_id': _get_row_value(row, 'MediaID'),
                'media_path': _get_row_value(row, 'MediaPath', ''),
                'media_file': _get_row_value(row, 'MediaFile', ''),
                'caption': _get_row_value(row, 'Caption', ''),
                'description': _get_row_value(row, 'Description', ''),
            })

        return media_items

    def _format_media_url(self, media: Dict) -> str:
        """Format media URL for Hugo."""
        media_path = media['media_path']
        media_file = media['media_file']

        # Strip RootsMagic's ?\  prefix if present
        if media_path.startswith('?\\'):
            media_path = media_path[2:]
        elif media_path.startswith('?/'):
            media_path = media_path[2:]

        # Combine path components
        if media_path:
            full_path = f"{self.media_base_path}{media_path}/{media_file}"
        else:
            full_path = f"{self.media_base_path}{media_file}"

        # Normalize path separators for web
        full_path = full_path.replace('\\', '/')

        return full_path

    def _generate_index_page(
        self,
        person_ids: List[int],
        output_dir: Path,
    ) -> Path:
        """Generate _index.md listing all exported people."""

        def _build_index(db: RMDatabase) -> str:
            lines = []

            # Front matter
            lines.append("---")
            lines.append("title: \"Family Biographies\"")
            lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
            lines.append("---")
            lines.append("")
            lines.append("# Family Biographies")
            lines.append("")
            lines.append("Browse biographies of family members:")
            lines.append("")

            # Get all people and sort by birth year
            people = []
            query = QueryService(db)

            for person_id in person_ids:
                person = query.get_person_with_primary_name(person_id)
                if person:
                    full_name = format_full_name(
                        given=_get_row_value(person, "Given"),
                        surname=_get_row_value(person, "Surname"),
                        prefix=_get_row_value(person, "Prefix"),
                        suffix=_get_row_value(person, "Suffix"),
                    )
                    birth_year = _get_row_value(person, "BirthYear")
                    death_year = _get_row_value(person, "DeathYear")
                    slug = _slugify(full_name)

                    people.append({
                        'name': full_name,
                        'birth_year': birth_year or 0,
                        'death_year': death_year,
                        'slug': slug,
                    })

            # Sort by birth year
            people.sort(key=lambda x: x['birth_year'])

            # Generate list
            for person in people:
                lifespan = ""
                if person['birth_year'] or person['death_year']:
                    b = person['birth_year'] or '?'
                    d = person['death_year'] or '?'
                    lifespan = f" ({b}–{d})"

                lines.append(f"- [{person['name']}]({person['slug']}/){lifespan}")

            lines.append("")
            lines.append(f"*{len(people)} biographies • Generated {datetime.now().strftime('%Y-%m-%d')}*")

            return "\n".join(lines)

        if self._db:
            content = _build_index(self._db)
        elif self.db_path:
            with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
                content = _build_index(db)
        else:
            raise ValueError("No database provided")

        index_file = output_dir / "_index.md"
        index_file.write_text(content, encoding='utf-8')

        return index_file
