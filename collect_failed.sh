#!/usr/bin/env bash
# Moves BMPs from ./failed_2025*/ into ./aggregate_failed/,
# then deletes failed_log*.csv and removes the failed_2025* dirs.

set -Eeuo pipefail

# Ensure the destination exists
mkdir -p "./aggregate_failed"

# Move *.bmp files from immediate children of each failed_2025* directory (non-recursive)
shopt -s nullglob
for d in ./failed_2025*/ ; do
  [[ -d "$d" ]] || continue
  for f in "$d"*.bmp "$d"*.BMP; do
    [[ -e "$f" ]] || continue
    mv -n -- "$f" "./aggregate_failed/"
  done
done
shopt -u nullglob

# Delete CSV logs in the current directory
rm -f -- ./failed_log*.csv

# Remove all failed_2025* directories
for d in ./failed_2025*/ ; do
  [[ -d "$d" ]] || continue
  rm -rf -- "$d"
done

echo "Consolidation complete. ✅"
