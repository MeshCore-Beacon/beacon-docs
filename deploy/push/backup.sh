#!/bin/sh
# Daily relay backup: snapshot the database, keep 14 days. Copy the files off the box separately.
set -eu
cd /opt/docker/beacon-push
docker exec beacon-push beacon-push admin backup "/data/backup-$(date +%F).db"
find data -name 'backup-*.db' -mtime +13 -delete
