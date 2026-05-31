#!/usr/bin/env bash
# Release the Sunbank HA integration: tag the current commit and publish a GitHub
# Release whose notes HACS shows as the update description.
#
# It reads the version from custom_components/sunbank/manifest.json and pulls the
# matching "## v<version> ..." section out of CHANGELOG.md — so the single place you
# write release notes is the changelog. Bump the manifest version + add a changelog
# section, commit, then run this.
#
#   ./release.sh
#
set -euo pipefail
cd "$(dirname "$0")"

VERSION=$(grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]+"' custom_components/sunbank/manifest.json | sed -E 's/.*"([^"]+)"$/\1/')
TAG="v${VERSION}"

# The changelog section for this version: from its "## v<version>" heading to the next "## ".
NOTES=$(awk -v tag="## ${TAG} " '
  $0 ~ "^"tag { grab=1; title=$0; sub(/^## /,"",title); next }
  grab && /^## / { exit }
  grab { print }
' CHANGELOG.md | sed -e 's/[[:space:]]*$//')
TITLE=$(grep -E "^## ${TAG} " CHANGELOG.md | head -1 | sed -E 's/^## //')

if [ -z "${TITLE:-}" ]; then
  echo "✗ No '## ${TAG}' section found in CHANGELOG.md — add one first." >&2
  exit 1
fi
if git rev-parse "${TAG}" >/dev/null 2>&1 || gh release view "${TAG}" >/dev/null 2>&1; then
  echo "✗ ${TAG} already released. Bump the version in manifest.json first." >&2
  exit 1
fi

echo "Releasing ${TITLE}"
git tag "${TAG}"
git push origin "${TAG}"
gh release create "${TAG}" --title "${TITLE}" --notes "${NOTES}"
echo "✓ Published ${TAG}"
