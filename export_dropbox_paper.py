#!/usr/bin/env python3
"""Export Dropbox Paper `.paper` files under a directory to Markdown or HTML."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Sequence

import dropbox
from dropbox.exceptions import ApiError, AuthError

DROPBOX_TIMEOUT_SECONDS = 30


def iter_paper_files(root: Path) -> Iterable[Path]:
    """Yield `.paper` files beneath `root`, sorted for deterministic output."""
    return sorted(root.rglob("*.paper"))


def compute_remote_path(local_file: Path, dropbox_root: Path) -> str:
    """Return the Dropbox remote path for `local_file` relative to `dropbox_root`."""
    try:
        relative = local_file.resolve().relative_to(dropbox_root.resolve())
    except ValueError as error:
        raise RuntimeError(
            f"{local_file} is not inside the Dropbox root {dropbox_root}"
        ) from error
    return "/" + relative.as_posix()


def export_paper(
    client: dropbox.Dropbox,
    remote_path: str,
    export_format: str,
) -> str:
    """Download the Paper doc at `remote_path` in the requested format."""
    try:
        metadata, response = client.files_export(
            remote_path, export_format=export_format
        )
    except ApiError as error:
        raise RuntimeError(f"Dropbox export failed: {error}") from error

    try:
        text = response.content.decode("utf-8")
    except UnicodeDecodeError:
        text = response.content.decode("utf-8", errors="replace")

    title = getattr(metadata, "name", remote_path.rsplit("/", 1)[-1])
    suffix = f" (exported as {export_format})" if export_format else ""
    return f"# {title}{suffix}\n\n{text}"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Export all Dropbox Paper `.paper` files under a directory."
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        required=True,
        help="Directory containing .paper files (processed recursively).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where converted files will be written.",
    )
    parser.add_argument(
        "--dropbox-token",
        help="Dropbox API access token (falls back to DROPBOX_ACCESS_TOKEN).",
    )
    parser.add_argument(
        "--dropbox-root",
        type=Path,
        default=Path("~/Dropbox"),
        help="Local Dropbox root for resolving remote paths (default: ~/Dropbox).",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "html"),
        default="markdown",
        help="Export format to request from Dropbox (default: markdown).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point."""
    args = parse_args(argv)
    paper_dir = args.paper_dir.expanduser()
    output_dir = args.output_dir.expanduser()
    dropbox_root = args.dropbox_root.expanduser()

    if not paper_dir.is_dir():
        raise SystemExit(f"--paper-dir must point to a directory: {paper_dir}")

    token = args.dropbox_token or os.environ.get("DROPBOX_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "Dropbox access token missing. Provide --dropbox-token or set DROPBOX_ACCESS_TOKEN."
        )

    client = dropbox.Dropbox(token, timeout=DROPBOX_TIMEOUT_SECONDS)
    output_dir.mkdir(parents=True, exist_ok=True)

    extension = ".md" if args.format == "markdown" else ".html"
    paper_files = list(iter_paper_files(paper_dir))
    if not paper_files:
        print(f"No .paper files found under {paper_dir}")
        return 0

    for paper_path in paper_files:
        print(f"Processing {paper_path}")
        try:
            remote_path = compute_remote_path(paper_path, dropbox_root)
            content = export_paper(client, remote_path, args.format)
        except AuthError as error:
            raise SystemExit(f"Dropbox authentication failed: {error}") from error
        except RuntimeError as error:
            print(f"  Skipping: {error}")
            continue

        relative_target = paper_path.relative_to(paper_dir).with_suffix(extension)
        target_path = output_dir / relative_target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
