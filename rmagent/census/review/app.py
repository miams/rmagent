"""
Census review web application.

FastAPI + HTMX interface for reviewing and correcting extracted census entries.
Provides human-in-the-loop validation with keyboard shortcuts and field editing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from rmagent.census.sidecar import CensusSidecarDB
from rmagent.config.config import load_app_config

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Census Review UI", version="0.1.0")

# Templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Database connection (will be initialized on startup)
sidecar_db: Optional[CensusSidecarDB] = None


# Pydantic models for request/response
class EntryUpdate(BaseModel):
    """Update request for census entry field."""

    field_path: str  # e.g., "name", "age", "fields.income_wages"
    new_value: str
    notes: Optional[str] = None


class EntryAction(BaseModel):
    """Action request for census entry."""

    action: str  # "approve", "flag", "skip"
    notes: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    global sidecar_db
    try:
        config = load_app_config(require_llm_credentials=False)
        sidecar_db = CensusSidecarDB(config.census.db_url)
        sidecar_db.connect()
        logger.info("Connected to census sidecar database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    if sidecar_db:
        sidecar_db.close()
        logger.info("Closed database connection")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main review page."""
    stats = sidecar_db.get_stats()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": stats,
        },
    )


@app.get("/review/next", response_class=HTMLResponse)
async def get_next_entry(request: Request):
    """Get next pending entry for review."""
    # Query for next pending entry
    query = """
    SELECT
        ce.entry_id,
        ce.name,
        ce.age,
        ce.sex,
        ce.race,
        ce.birthplace,
        ce.occupation,
        ce.fields,
        ce.person_id,
        ce.match_confidence,
        ch.page_id,
        cp.census_year,
        cp.image_path
    FROM census_entry ce
    JOIN census_household ch ON ce.household_id = ch.household_id
    JOIN census_page cp ON ch.page_id = cp.page_id
    WHERE ce.review_status = 'pending'
    ORDER BY cp.census_year, cp.page_id, ch.household_id, ce.line_number
    LIMIT 1
    """

    result = sidecar_db.execute_one(query)

    if not result:
        return HTMLResponse("<p>No more entries to review!</p>")

    return templates.TemplateResponse(
        "entry_card.html",
        {
            "request": request,
            "entry": result,
        },
    )


@app.post("/review/{entry_id}/update")
async def update_entry_field(entry_id: int, update: EntryUpdate):
    """Update a field in a census entry."""
    try:
        # Determine if updating common field or JSONB field
        if update.field_path.startswith("fields."):
            # Update JSONB field
            jsonb_key = update.field_path.replace("fields.", "")
            query = """
            UPDATE census_entry
            SET fields = jsonb_set(fields, %s, %s, true),
                updated_at = CURRENT_TIMESTAMP
            WHERE entry_id = %s
            """
            sidecar_db.execute(query, ([jsonb_key], f'"{update.new_value}"', entry_id))
        else:
            # Update common field (name, age, etc.)
            # Note: Use parameterized query to prevent SQL injection
            query = f"""
            UPDATE census_entry
            SET {update.field_path} = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE entry_id = %s
            """
            sidecar_db.execute(query, (update.new_value, entry_id))

        # Log the update
        log_query = """
        INSERT INTO census_review_log
            (entry_id, reviewer_id, action, field_path, new_value, notes)
        VALUES (%s, %s, 'correct', %s, %s, %s)
        """
        sidecar_db.execute(
            log_query,
            (entry_id, "web_user", update.field_path, update.new_value, update.notes),
        )

        logger.info(f"Updated entry {entry_id}: {update.field_path} = {update.new_value}")

        return {"status": "ok", "entry_id": entry_id}

    except Exception as e:
        logger.error(f"Failed to update entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/review/{entry_id}/action")
async def entry_action(entry_id: int, action: EntryAction):
    """Perform action on census entry (approve, flag, skip)."""
    try:
        valid_actions = ["approve", "flag", "skip"]
        if action.action not in valid_actions:
            raise HTTPException(400, f"Invalid action. Must be one of: {valid_actions}")

        # Update review status
        status_map = {
            "approve": "approved",
            "flag": "flagged",
            "skip": "skipped",
        }
        new_status = status_map[action.action]

        query = """
        UPDATE census_entry
        SET review_status = %s,
            reviewed_by = 'web_user',
            reviewed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE entry_id = %s
        """
        sidecar_db.execute(query, (new_status, entry_id))

        # Log the action
        log_query = """
        INSERT INTO census_review_log
            (entry_id, reviewer_id, action, notes)
        VALUES (%s, %s, %s, %s)
        """
        sidecar_db.execute(log_query, (entry_id, "web_user", action.action, action.notes))

        logger.info(f"Entry {entry_id} {action.action}ed")

        return {"status": "ok", "entry_id": entry_id, "action": action.action}

    except Exception as e:
        logger.error(f"Failed to perform action on entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_class=HTMLResponse)
async def get_stats(request: Request):
    """Get current review statistics."""
    stats = sidecar_db.get_stats()

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "stats": stats,
        },
    )


def run_review_app(host: str = "127.0.0.1", port: int = 8000):
    """
    Run the review application.

    Args:
        host: Host to bind to
        port: Port to bind to

    Example:
        >>> run_review_app(port=8080)
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_review_app()
