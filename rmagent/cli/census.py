"""
Census extraction CLI commands.

Provides commands for cataloging, processing, and reviewing census extractions.
Uses PostgreSQL sidecar database with hybrid schema (columns + JSONB).
"""

import sys
from pathlib import Path

import click

from rmagent.census import catalog_census_media
from rmagent.census.pipeline import CensusPipeline, process_single_image
from rmagent.census.sidecar import CensusSidecarDB
from rmagent.config.config import load_app_config


@click.group()
def census():
    """Census extraction and processing commands."""
    pass


@census.command("catalog")
@click.option(
    "--database",
    "-d",
    help="Path to RootsMagic database (default: from config)",
    type=click.Path(exists=True),
)
@click.option(
    "--db-url",
    "-u",
    help="PostgreSQL connection string (default: from config CENSUS_DB_URL)",
    type=str,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output",
)
def catalog_command(database, db_url, verbose):
    """
    Catalog census media from RootsMagic database.

    Scans the RootsMagic database for census-related media files and
    populates the census sidecar PostgreSQL database with page metadata.

    Example:
        rmagent census catalog
        rmagent census catalog -d data/Iiams.rmtree -v
        rmagent census catalog -u postgresql://user:pass@localhost:5432/census_sidecar
    """
    # Load config for default values
    config = load_app_config()

    if not database:
        database = config.database.database_path

    if not db_url:
        db_url = config.census.db_url

    click.echo(f"Cataloging census media from: {database}")
    click.echo(f"PostgreSQL connection: {db_url.split('@')[0]}@****")  # Mask password
    click.echo()

    try:
        stats = catalog_census_media(database, db_url)

        click.echo("✅ Census media catalog complete!")
        click.echo()
        click.echo("Statistics:")
        click.echo(f"  Total media files found: {stats['total_media']}")
        click.echo(f"  Census events with media: {stats['census_events']}")
        click.echo(f"  Media with census year: {stats['media_with_year']}")
        click.echo(f"  Media without census year: {stats['media_without_year']}")

        if stats["errors"]:
            click.echo()
            click.echo(f"⚠️  Errors: {len(stats['errors'])}")
            if verbose:
                for error in stats["errors"]:
                    click.echo(f"  - {error}")

        if stats["media_without_year"] > 0:
            click.echo()
            click.echo(
                "⚠️  Some media files could not be matched to census years."
            )
            click.echo("   Review media captions/descriptions and update as needed.")

    except Exception as e:
        click.echo(f"❌ Error cataloging census media: {str(e)}", err=True)
        raise click.Abort()


@census.command("stats")
@click.option(
    "--db-url",
    "-u",
    help="PostgreSQL connection string (default: from config CENSUS_DB_URL)",
    type=str,
)
def stats_command(db_url):
    """
    Show census sidecar database statistics.

    Displays counts of pages, households, entries by year and review status.
    Uses PostgreSQL database with hybrid schema.

    Example:
        rmagent census stats
        rmagent census stats -u postgresql://user:pass@localhost:5432/census_sidecar
    """
    # Load config for default values
    config = load_app_config()

    if not db_url:
        db_url = config.census.db_url

    try:
        with CensusSidecarDB(db_url) as sidecar:
            stats = sidecar.get_stats()

        click.echo("Census Sidecar Database Statistics")
        click.echo("=" * 40)
        click.echo()
        click.echo(f"Total Pages: {stats['total_pages']}")
        click.echo(f"Total Households: {stats['total_households']}")
        click.echo(f"Total Entries: {stats['total_entries']}")
        click.echo()

        if stats['by_year']:
            click.echo("Pages by Census Year:")
            for year in sorted(stats['by_year'].keys()):
                count = stats['by_year'][year]
                click.echo(f"  {year}: {count} pages")
            click.echo()

        if stats['by_status']:
            click.echo("Review Status:")
            for status, count in stats['by_status'].items():
                click.echo(f"  {status}: {count} entries")
        else:
            click.echo("No census entries extracted yet.")

    except Exception as e:
        click.echo(f"❌ Error reading sidecar database: {str(e)}", err=True)
        raise click.Abort()


@census.command("process")
@click.argument("image_path", type=click.Path(exists=True))
@click.option(
    "--year",
    "-y",
    type=int,
    required=True,
    help="Census year (e.g., 1940)",
)
@click.option(
    "--database",
    "-d",
    help="Path to RootsMagic database (default: from config)",
    type=click.Path(exists=True),
)
@click.option(
    "--db-url",
    "-u",
    help="PostgreSQL connection string (default: from config)",
    type=str,
)
@click.option(
    "--media-root",
    "-m",
    help="Root directory for census images (default: from config)",
    type=click.Path(exists=True, file_okay=False),
)
def process_command(image_path, year, database, db_url, media_root):
    """
    Process a single census image through OCR pipeline.

    Runs the complete pipeline:
    1. Image preprocessing (deskew, denoise, CLAHE)
    2. Layout detection (table grid, cells)
    3. OCR extraction (Tesseract)
    4. Person matching (fuzzy match to RootsMagic)
    5. Database insertion (entries + provenance)

    Example:
        rmagent census process census_1940.jpg --year 1940
        rmagent census process "/path/to/1940, Ohio, Allen - Iiams, Joseph.jpg" -y 1940
    """
    # Load config
    config = load_app_config(require_llm_credentials=False)

    if not database:
        database = config.database.database_path

    if not db_url:
        db_url = config.census.db_url

    if not media_root and config.database.media_root_directory:
        media_root = config.database.media_root_directory

    click.echo(f"Processing: {Path(image_path).name}")
    click.echo(f"Census Year: {year}")
    click.echo()

    try:
        # Create pipeline
        pipeline = CensusPipeline(
            rm_database_path=Path(database),
            census_db_url=db_url,
            media_root=Path(media_root) if media_root else None,
        )

        # Process image
        result = pipeline.process_image(image_path, year)

        # Display results
        click.echo()
        if result.success:
            click.echo("✅ Processing successful!")
            click.echo()
            click.echo("Metrics:")
            click.echo(f"  Preprocessing:    {result.preprocessing_time:.2f}s")
            click.echo(f"  Layout Detection: {result.layout_detection_time:.2f}s ({result.num_cells_detected} cells)")
            click.echo(f"  OCR Extraction:   {result.ocr_time:.2f}s ({result.num_cells_extracted} fields, avg conf: {result.avg_ocr_confidence:.2f})")
            click.echo(f"  Person Matching:  ({result.num_persons_matched} matched, avg conf: {result.avg_match_confidence:.2f})")
            click.echo(f"  Database Insert:  {result.database_time:.2f}s ({result.num_entries_created} entries)")
            click.echo(f"  Total Time:       {result.total_time:.2f}s")
            click.echo()
            click.echo(f"Created {result.num_entries_created} census entries in database.")
        else:
            click.echo(f"❌ Processing failed: {result.error_message}", err=True)
            sys.exit(1)

        pipeline.close()

    except Exception as e:
        click.echo(f"❌ Error processing image: {str(e)}", err=True)
        raise click.Abort()


@census.command("process-batch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--year",
    "-y",
    type=int,
    required=True,
    help="Census year for all images (e.g., 1940)",
)
@click.option(
    "--limit",
    "-n",
    type=int,
    help="Maximum number of images to process",
)
@click.option(
    "--pattern",
    "-p",
    default="*.jpg",
    help="File pattern to match (default: *.jpg)",
)
@click.option(
    "--database",
    "-d",
    help="Path to RootsMagic database (default: from config)",
    type=click.Path(exists=True),
)
@click.option(
    "--db-url",
    "-u",
    help="PostgreSQL connection string (default: from config)",
    type=str,
)
@click.option(
    "--media-root",
    "-m",
    help="Root directory for census images (default: from config)",
    type=click.Path(exists=True, file_okay=False),
)
def process_batch_command(directory, year, limit, pattern, database, db_url, media_root):
    """
    Process multiple census images from a directory.

    Runs the full OCR pipeline on all matching images in the directory.
    Progress and metrics are displayed for each image.

    Example:
        rmagent census process-batch "/path/to/1940 Federal/" --year 1940
        rmagent census process-batch ~/census/1940/ -y 1940 --limit 10
        rmagent census process-batch ~/census/1940/ -y 1940 --pattern "*.jpg"
    """
    # Load config
    config = load_app_config(require_llm_credentials=False)

    if not database:
        database = config.database.database_path

    if not db_url:
        db_url = config.census.db_url

    if not media_root and config.database.media_root_directory:
        media_root = config.database.media_root_directory

    # Find images
    directory = Path(directory)
    image_paths = sorted(directory.glob(pattern))

    if limit:
        image_paths = image_paths[:limit]

    if not image_paths:
        click.echo(f"❌ No images found matching '{pattern}' in {directory}", err=True)
        sys.exit(1)

    click.echo(f"Batch Processing Census Images")
    click.echo("=" * 70)
    click.echo(f"Directory:    {directory}")
    click.echo(f"Census Year:  {year}")
    click.echo(f"Pattern:      {pattern}")
    click.echo(f"Total Images: {len(image_paths)}")
    if limit:
        click.echo(f"Limit:        {limit} images")
    click.echo("=" * 70)
    click.echo()

    try:
        # Create pipeline
        pipeline = CensusPipeline(
            rm_database_path=Path(database),
            census_db_url=db_url,
            media_root=Path(media_root) if media_root else None,
        )

        # Process batch
        batch_result = pipeline.process_batch(image_paths, year, show_progress=True)

        # Close pipeline
        pipeline.close()

        # Exit with error code if any failed
        if batch_result.failed > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Processing interrupted by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Batch processing error: {str(e)}", err=True)
        raise click.Abort()


@census.command("review")
@click.option(
    "--port",
    "-p",
    type=int,
    default=8000,
    help="Port for web server (default: 8000)",
)
@click.option(
    "--db-url",
    "-u",
    help="PostgreSQL connection string (default: from config)",
    type=str,
)
def review_command(port, db_url):
    """
    Launch web-based review UI for census entries.

    Opens a local web server with HTMX-powered interface for:
    - Reviewing OCR extractions
    - Approving or correcting entries
    - Flagging uncertain data
    - Viewing provenance and confidence scores

    The UI will be available at http://127.0.0.1:PORT

    Example:
        rmagent census review
        rmagent census review --port 8080
    """
    # Load config
    config = load_app_config(require_llm_credentials=False)

    if not db_url:
        db_url = config.census.db_url

    click.echo("Starting Census Review UI...")
    click.echo(f"Database: {db_url.split('@')[0]}@****")
    click.echo(f"Port: {port}")
    click.echo()
    click.echo(f"🌐 Open browser to: http://127.0.0.1:{port}")
    click.echo()
    click.echo("Press Ctrl+C to stop the server")
    click.echo()

    try:
        # Import here to avoid loading heavy dependencies if not needed
        from rmagent.census.review import run_review_app

        run_review_app(port=port, db_url=db_url)

    except KeyboardInterrupt:
        click.echo("\n\n✅ Review server stopped")
    except Exception as e:
        click.echo(f"\n❌ Error starting review UI: {str(e)}", err=True)
        raise click.Abort()
