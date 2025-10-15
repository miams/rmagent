"""
Census extraction CLI commands.

Provides commands for cataloging, processing, and reviewing census extractions.
"""

import click

from rmagent.census import catalog_census_media
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
    "--sidecar",
    "-s",
    help="Path to census sidecar database (default: data/census/sidecar/census.db)",
    type=click.Path(),
    default="data/census/sidecar/census.db",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output",
)
def catalog_command(database, sidecar, verbose):
    """
    Catalog census media from RootsMagic database.

    Scans the RootsMagic database for census-related media files and
    populates the census sidecar database with page metadata.

    Example:
        rmagent census catalog
        rmagent census catalog -d data/Iiams.rmtree -s data/census.db -v
    """
    # Load config if database path not provided
    if not database:
        config = load_app_config()
        database = config.rm_database_path

    click.echo(f"Cataloging census media from: {database}")
    click.echo(f"Sidecar database: {sidecar}")
    click.echo()

    try:
        stats = catalog_census_media(database, sidecar)

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
    "--sidecar",
    "-s",
    help="Path to census sidecar database",
    type=click.Path(exists=True),
    default="data/census/sidecar/census.db",
)
def stats_command(sidecar):
    """
    Show census sidecar database statistics.

    Displays counts of pages, households, entries, and review status.

    Example:
        rmagent census stats
        rmagent census stats -s data/census.db
    """
    import sqlite3

    try:
        conn = sqlite3.connect(sidecar)

        # Get page counts by year
        pages_by_year = conn.execute(
            """
            SELECT census_year, COUNT(*) as page_count
            FROM census_page
            GROUP BY census_year
            ORDER BY census_year
            """
        ).fetchall()

        # Get review status counts
        review_stats = conn.execute(
            """
            SELECT review_status, COUNT(*) as entry_count
            FROM census_entry
            GROUP BY review_status
            ORDER BY entry_count DESC
            """
        ).fetchall()

        # Get total counts
        total_pages = conn.execute(
            "SELECT COUNT(*) FROM census_page"
        ).fetchone()[0]
        total_households = conn.execute(
            "SELECT COUNT(*) FROM census_household"
        ).fetchone()[0]
        total_entries = conn.execute(
            "SELECT COUNT(*) FROM census_entry"
        ).fetchone()[0]

        conn.close()

        click.echo("Census Sidecar Database Statistics")
        click.echo("=" * 40)
        click.echo()
        click.echo(f"Total Pages: {total_pages}")
        click.echo(f"Total Households: {total_households}")
        click.echo(f"Total Entries: {total_entries}")
        click.echo()

        if pages_by_year:
            click.echo("Pages by Census Year:")
            for year, count in pages_by_year:
                click.echo(f"  {year}: {count} pages")
            click.echo()

        if review_stats:
            click.echo("Review Status:")
            for status, count in review_stats:
                click.echo(f"  {status}: {count} entries")
        else:
            click.echo("No census entries extracted yet.")

    except Exception as e:
        click.echo(f"❌ Error reading sidecar database: {str(e)}", err=True)
        raise click.Abort()
