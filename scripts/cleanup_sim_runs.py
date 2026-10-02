#!/usr/bin/env python3
"""
Cleanup utility to remove simulated run records from the delays database.
Deletes all records where github_run_id starts with 'sim-'.
"""

import sqlite3
from pathlib import Path

# Paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "delays.db"


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def cleanup_sim_runs(conn: sqlite3.Connection) -> int:
    """
    Delete all records where github_run_id starts with 'sim-'.
    
    Returns:
        Number of records deleted.
    """
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM delays WHERE github_run_id LIKE 'sim-%'")
        count_before = cursor.fetchone()["count"]
        
        cursor.execute("DELETE FROM delays WHERE github_run_id LIKE 'sim-%'")
        
        cursor.execute("SELECT COUNT(*) as count FROM delays")
        count_after = cursor.fetchone()["count"]
    
    return count_before, count_after


def main():
    db_path = DEFAULT_DB_PATH
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = get_db_connection(db_path)
    
    print(f"Connecting to database: {db_path}")
    
    # Check current state
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM delays")
    total_before = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM delays WHERE github_run_id LIKE 'sim-%'")
    sim_count = cursor.fetchone()["count"]
    
    print(f"Total records before cleanup: {total_before}")
    print(f"Simulated records (github_run_id LIKE 'sim-%'): {sim_count}")
    
    if sim_count == 0:
        print("No simulated records found. Database is clean.")
        conn.close()
        return
    
    # Perform cleanup
    print(f"\nRemoving {sim_count} simulated records...")
    before, after = cleanup_sim_runs(conn)
    
    print(f"Records deleted: {before}")
    print(f"Total records remaining: {after}")
    
    # Export JSON after cleanup
    from record_delay import DEFAULT_JSON_PATHS, export_data_to_json
    
    print(f"\nExporting cleaned data to JSON snapshots...")
    exported = export_data_to_json(conn, output_paths=DEFAULT_JSON_PATHS)
    summary = exported["summary"]
    print(f"  Total Runs:          {summary['total_runs']}")
    print(f"  Last Week Avg:       {summary['last_week_avg_minutes']} min")
    print(f"  Last Month Avg:      {summary['last_month_avg_minutes']} min")
    print("  Yearly Averages:")
    for y in summary["yearly_averages"]:
        print(f"    - {y['year']}: {y['avg_delay_minutes']} min ({y['run_count']} runs)")
    
    conn.close()
    print("\nCleanup complete!")


if __name__ == "__main__":
    main()
