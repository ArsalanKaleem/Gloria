# Admin Workflow

## Adding a new PDF (HEC or university)

1. Drop the PDF into `data/hec/<subfolder>/` or `data/university/<subfolder>/`.
2. Next to it, create a sidecar `<same-name>.meta.json` describing the source:
   ```json
   {
     "title": "Undergraduate Prospectus 2025",
     "organization": "Shaikh Ayaz University",
     "source_url": "https://example.sau.edu.pk/...",
     "published": "2025-01-15"
   }
   ```
3. Run the extract + index pipeline:
   ```bash
   docker compose exec backend python -m scripts.ingest_pdfs
   docker compose exec backend python -m scripts.index_documents
   ```
4. Gloria uses the new PDF **immediately** — no restart, no retraining.

## Adding a new person / department / program

1. Create a JSON file under `data/university/<people|departments|programs|officers>/`.
   Copy one of the `EXAMPLE_*.json` files as a template.
2. Load it into Postgres:
   ```bash
   docker compose exec backend python -m scripts.load_university
   ```
3. The loader upserts by `id` — safe to re-run.

## Issuing an API key

```bash
docker compose exec backend python -m scripts.create_api_key sau-portal 2000
```

The command prints the `FULL KEY` **once**. Store it in your secret
manager and paste it into the calling application's environment.

## Rotating a key

Set the key's `active` column to false in Postgres (or add an admin
endpoint). Then issue a fresh key.

## Removing a document

Delete the sidecar's `.pdf` and its `.meta.json`, then rerun
`index_documents.py`. Old chunks with the same sha1 stay in Chroma until
you call `vector_store.delete_where({"sha1": <hash>})` — add an admin
command for that when you build the dashboard.
