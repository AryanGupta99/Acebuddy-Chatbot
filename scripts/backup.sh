#!/bin/bash
# Backup script for AceBuddy RAG system
# Backs up data, embeddings, and configuration for migration/recovery

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="acebuddy_backup_${TIMESTAMP}"
FULL_BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "Starting AceBuddy RAG backup..."
echo "Backup destination: ${FULL_BACKUP_PATH}"

# Create backup directory
mkdir -p "${FULL_BACKUP_PATH}"

# Backup data files
echo "Backing up data files..."
cp -r data/kb "${FULL_BACKUP_PATH}/"
cp -r data/chroma "${FULL_BACKUP_PATH}/" 2>/dev/null || echo "Warning: chroma directory may not exist yet"
cp data/processed_chunks.json "${FULL_BACKUP_PATH}/" 2>/dev/null || echo "Warning: processed_chunks.json not found"

# Backup configuration
echo "Backing up configuration..."
cp .env "${FULL_BACKUP_PATH}/.env.backup" 2>/dev/null || echo "Warning: .env file not found"
cp requirements.txt "${FULL_BACKUP_PATH}/"
cp docker-compose.yml "${FULL_BACKUP_PATH}/"
cp Dockerfile "${FULL_BACKUP_PATH}/" 2>/dev/null || echo "Dockerfile not in root (expected)"

# Backup app code
echo "Backing up application code..."
cp -r app "${FULL_BACKUP_PATH}/"
cp -r scripts "${FULL_BACKUP_PATH}/"

# Create backup metadata
echo "Creating backup metadata..."
cat > "${FULL_BACKUP_PATH}/BACKUP_INFO.txt" << EOF
AceBuddy RAG System Backup
==========================
Backup Date: $(date)
Hostname: $(hostname)
Timestamp: ${TIMESTAMP}

Contents:
- kb/ : Knowledge base files
- chroma/ : Vector database index
- processed_chunks.json : Processed and embedded chunks
- app/ : FastAPI application code
- scripts/ : Utility scripts
- requirements.txt : Python dependencies
- docker-compose.yml : Docker orchestration config
- .env.backup : Environment configuration

To restore:
1. Copy all contents to target system
2. Update .env file with target server details
3. Run: docker-compose up --build
EOF

# Compress backup
echo "Compressing backup..."
tar -czf "${FULL_BACKUP_PATH}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}" 2>/dev/null || {
    echo "Warning: Could not compress to tar.gz (may not be available on Windows)"
}

# Create checksum
echo "Creating checksum..."
cd "${FULL_BACKUP_PATH}"
find . -type f -exec sha256sum {} \; > CHECKSUMS.txt 2>/dev/null || echo "Note: sha256sum not available"
cd - > /dev/null

echo ""
echo "✓ Backup completed successfully!"
echo "Backup location: ${FULL_BACKUP_PATH}"
echo ""
echo "To restore this backup:"
echo "1. Copy entire directory to target system"
echo "2. Update .env with new environment settings"
echo "3. Run: docker-compose up --build -d"
echo ""
