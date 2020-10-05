docker run --rm \
  --env PROJECT_ID="for-simon" \
  --env TABLE_ID="urls.status" \
  --env GOOGLE_APPLICATION_CREDENTIALS=/credentials.json \
  --mount type=bind,source=$HOME/credentials.json,target=/credentials.json,readonly \
  urlbuilder scielo coronvirus virus 30
