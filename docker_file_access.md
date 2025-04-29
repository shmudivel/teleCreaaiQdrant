# Accessing Generated Files in Docker Container

## Finding Your Docker Containers

To see all running Docker containers:

```bash
docker ps
```

Look for containers with names like `telecreaaiqdrant-bot-1`.

## Accessing Output Directories

To list all output directories in the container:

```bash
docker exec -it telecreaaiqdrant-bot-1 ls -la /app
```

The output directories will have names like `output_YYYYMMDD_HHMMSS` (e.g., `output_20250425_122717`).

## Viewing Generated Content

### Top Reels Files

To view the top reels metadata files:

```bash
docker exec -it telecreaaiqdrant-bot-1 ls -la /app/output_YYYYMMDD_HHMMSS/top_reels
```

### Final Reels Files

To view the final edited reels:

```bash
docker exec -it telecreaaiqdrant-bot-1 ls -la /app/output_YYYYMMDD_HHMMSS/final_reels
```

## Viewing Content of Specific Files

To view the content of a specific metadata file:

```bash
docker exec -it telecreaaiqdrant-bot-1 cat /app/output_YYYYMMDD_HHMMSS/top_reels/metadata_XX.json
```

To view the content of a final edited file:

```bash
docker exec -it telecreaaiqdrant-bot-1 cat /app/output_YYYYMMDD_HHMMSS/final_reels/final_heygen_XX.txt
```

## Copying Files from Docker to Local Machine

If you want to copy files from the Docker container to your local machine:

```bash
docker cp telecreaaiqdrant-bot-1:/app/output_YYYYMMDD_HHMMSS/final_reels ./local_destination
```

Replace:
- `YYYYMMDD_HHMMSS` with the actual timestamp of the output directory
- `XX` with the actual file number
- `./local_destination` with your desired local directory path 