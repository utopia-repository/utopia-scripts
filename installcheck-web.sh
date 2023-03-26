#!/bin/bash
# Run installcheck regularly, saving the results to the website and reporting checker status to a webhook.

DATE_PART="$(date +%Y%m%d-%s)"
OUTPUT_DIR="/srv/aptly-web/installcheck/${DATE_PART}"
#OUTPUT_DIR="/tmp/installcheck/${DATE_PART}"
URL="https://deb-master.utopia-repository.org/installcheck/${DATE_PART}"

script_dir="$(realpath "${0%/*}")"

mkdir -p "$OUTPUT_DIR" || exit 1
cd "$OUTPUT_DIR" || exit 1

# TODO: this should report if some Packages list failed to download
"$script_dir"/installcheck.py

failed_count=$(find . -maxdepth 1 -type f | wc -l)
if [[ failed_count -ge 0 ]]; then
    echo "The following dists failed installability checks:"
    ls -l
    webhook_text="${failed_count} installability check(s) failed: ${URL}"
else
    webhook_text="All installability checks passed"
    echo "$webhook_text"
fi

if [[ -n "$WEBHOOK_URL" ]]; then
    echo "Sending webhook announcement..."
    curl -d "{\"text\":\"$webhook_text\"}" -H 'Content-Type: application/json' \
        "$WEBHOOK_URL"
fi
