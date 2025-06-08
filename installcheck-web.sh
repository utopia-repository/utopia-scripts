#!/bin/bash
# Run installcheck regularly, saving the results to the website and reporting checker status to a webhook.
shopt -s nullglob

DATE_PART="$(date +%Y%m%d-%s)"
OUTPUT_DIR="/srv/aptly-web/installcheck/${DATE_PART}"
URL_BASE="https://deb-master.utopia-repository.org/installcheck/${DATE_PART}"

script_dir="$(realpath "${0%/*}")"

mkdir -p "$OUTPUT_DIR" || exit 1
cd "$OUTPUT_DIR" || exit 1

# TODO: this should report if some Packages list failed to download
"$script_dir"/installcheck.py "$@"

webhook_text=""
for report in *.txt; do
    webhook_text+=$"Installability check failed: ${URL_BASE}/${report}\n"
done
if [[ -z "$webhook_text" ]]; then
    webhook_text="All installability checks passed"
fi

echo -e "$webhook_text"

if [[ -n "$WEBHOOK_URL" ]]; then
    echo "Sending webhook announcement..."
    echo -n "Webhook response: "
    curl -d "{\"text\":\"$webhook_text\"}" -H 'Content-Type: application/json' \
        "$WEBHOOK_URL"
fi
