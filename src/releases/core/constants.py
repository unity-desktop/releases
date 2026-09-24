"""
Constants.
"""

APP = "releases"
SUITES_DIR = "suites"

REGISTRY = "ghcr.io/unity-desktop/oci-packages"
REPOSITORY = "ghcr.io/unity-desktop/ubuntu"
OWNER = "https://github.com/unity-desktop"

UPLOAD_TYPE = "application/vnd.debian.upload.v1"
MANIFEST_TYPE = "application/vnd.oci.image.manifest.v1+json"
FILE_TYPE = "application/octet-stream"

TITLE = "org.opencontainers.image.title"
SOURCE = "org.opencontainers.image.source"
REVISION = "org.opencontainers.image.revision"
CREATED = "org.opencontainers.image.created"

# Debian Policy 5.6.1.
SOURCE_NAME = r"^[a-z0-9][a-z0-9+.-]+$"

# Layer titles of the repository indices.
PACKAGES_INDEX = "dists/{suite}/*/binary-*/Packages"
SOURCES_INDEX = "dists/{suite}/*/source/Sources"
