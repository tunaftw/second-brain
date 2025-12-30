#!/usr/bin/env python3
"""Migrate existing data to new library structure.

Moves:
- data/transcripts/youtube/* → data/raw/youtube/{channel}/
- data/nuggets/* → data/analysis/youtube/{channel}/

Run with: python scripts/migrate_to_library.py
Add --dry-run to preview without making changes.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nuggets.library import LibraryPaths, slugify


def migrate_transcripts(dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Migrate transcript files to raw/ structure.

    Returns:
        List of (old_path, new_path) tuples for migrated files.
    """
    old_dir = Path("data/transcripts/youtube")
    if not old_dir.exists():
        print("No transcripts to migrate")
        return []

    paths = LibraryPaths()
    migrations: list[tuple[Path, Path]] = []

    for old_file in old_dir.glob("*.txt"):
        # Parse filename: channel-date-videoid.txt
        # Example: chris-williamson-2025-12-25-hLIvhTiytIE.txt
        parts = old_file.stem.rsplit("-", 4)  # Split from right to get video_id
        if len(parts) < 4:
            print(f"  Skipping {old_file.name}: unexpected format")
            continue

        # Reconstruct parts
        video_id = parts[-1]
        day = parts[-2]
        month = parts[-3]
        year = parts[-4]
        channel = "-".join(parts[:-4]) if len(parts) > 4 else "unknown"

        date = f"{year}-{month}-{day}"

        # New path (as JSON with transcript content)
        new_path = paths.base / "raw" / "youtube" / channel / f"{date}-{video_id}.json"

        migrations.append((old_file, new_path))

        if dry_run:
            print(f"  Would move: {old_file} → {new_path}")
        else:
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Read transcript and save as JSON
            content = old_file.read_text(encoding="utf-8")
            data = {
                "video_id": video_id,
                "channel_slug": channel,
                "date": date,
                "transcript": content,
                "source_file": str(old_file),
            }
            new_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  Migrated: {old_file.name} → {new_path}")

    return migrations


def migrate_nuggets(dry_run: bool = False) -> list[tuple[Path, Path]]:
    """Migrate nugget files to analysis/ structure.

    Returns:
        List of (old_path, new_path) tuples for migrated files.
    """
    old_dir = Path("data/nuggets")
    if not old_dir.exists():
        print("No nuggets to migrate")
        return []

    paths = LibraryPaths()
    migrations: list[tuple[Path, Path]] = []

    for old_file in old_dir.glob("*.json"):
        if old_file.name == ".gitkeep":
            continue

        # Load episode data to get channel info
        try:
            data = json.loads(old_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  Skipping {old_file.name}: invalid JSON")
            continue

        source_name = data.get("source_name", "unknown")
        channel_slug = slugify(source_name)

        # Extract date from episode data or ID
        date_str = None
        if data.get("date"):
            # Parse ISO date
            date_str = data["date"][:10]  # "2025-12-25T00:00:00" → "2025-12-25"
        else:
            # Try to extract from ID: youtube-2025-12-25-hLIvhTiE
            episode_id = data.get("id", "")
            parts = episode_id.split("-")
            if len(parts) >= 4:
                date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"

        if not date_str:
            date_str = "unknown"

        # Extract video_id from URL or ID
        video_id = "unknown"
        url = data.get("url", "")
        if "v=" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        elif data.get("id"):
            video_id = data["id"].split("-")[-1]

        # New path
        new_path = paths.analysis_youtube(source_name, date_str, video_id)

        migrations.append((old_file, new_path))

        if dry_run:
            print(f"  Would move: {old_file} → {new_path}")
        else:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_file, new_path)
            print(f"  Migrated: {old_file.name} → {new_path}")

    return migrations


def main():
    """Run migration."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate data to library structure")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    print("=" * 60)
    print("Migrating to Library Structure")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN - No changes will be made]\n")

    # Ensure library directories exist
    if not args.dry_run:
        paths = LibraryPaths()
        paths.ensure_dirs()
        print("Created library directories\n")

    # Migrate transcripts
    print("Migrating transcripts...")
    transcript_migrations = migrate_transcripts(dry_run=args.dry_run)

    # Migrate nuggets
    print("\nMigrating nuggets...")
    nugget_migrations = migrate_nuggets(dry_run=args.dry_run)

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Transcripts: {len(transcript_migrations)} files")
    print(f"  Nuggets: {len(nugget_migrations)} files")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes")
    else:
        print("\nMigration complete!")
        print("\nNote: Original files were kept. Delete manually after verification:")
        print("  rm -rf data/transcripts/")
        print("  rm -rf data/nuggets/")


if __name__ == "__main__":
    main()
