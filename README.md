# Dropbox Paper Export

This Python script is for people who want to bulk convert their .paper files
into a format that can be read and stored elsewhere.

The script walks a directory of Dropbox Paper `.paper` files, downloads the
underlying documents via the Dropbox SDK, and writes them out as Markdown or
HTML files. The folder layout under the output directory mirrors the structure
found in the input directory.

Written with the help of AI.

## Prerequisites

1. **Python environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Dropbox API token**
   - Create a Dropbox app with permission to read files metadata and content.
   - Generate an access token and expose it to the script:
     ```bash
     export DROPBOX_ACCESS_TOKEN=your_token_here
     ```
     or pass `--dropbox-token` on the command line.

## Usage

Run the exporter by pointing it at the directory that contains your `.paper`
files and the directory where you want the converted files written:

```bash
python export_dropbox_paper.py \
  --paper-dir ~/Dropbox/Migrated\ Paper\ Docs \
  --output-dir ./exports \
  --format markdown
```

Flags:

- `--paper-dir` — directory that holds the `.paper` files (processed recursively).
- `--output-dir` — directory where converted files are written.
- `--format` — `markdown` (default) or `html`.
- `--dropbox-root` — path to your local Dropbox root, used to compute the remote
  path for each `.paper` file (default: `~/Dropbox`).
- `--dropbox-token` — access token to use instead of the `DROPBOX_ACCESS_TOKEN`
  environment variable.

## Notes

- Each `.paper` file must live under the Dropbox root (default `~/Dropbox`). If a
  file falls outside that tree, the script skips it and reports the reason.
- Output files inherit the source names: `Example.paper` becomes `Example.md`
  (or `.html`) in the output directory.
- If the Dropbox API returns an error for a document, the script prints the
  message and continues with the remaining files.
