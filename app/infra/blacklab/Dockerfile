# =============================================================================
# CO.RA.PAN BlackLab security overlay image
# =============================================================================
#
# Same BlackLab build as before (5.0.0-SNAPSHOT, built 2026-01-12, upstream
# digest below); the only change is the Ubuntu security update of libbrotli1
# for CVE-2026-111497 (USN-8956-1, fixed in 1.1.0-2ubuntu0.1 on noble).
# User, CMD, working directory, volumes and ports are inherited unchanged.
#
# Built locally and published to the server by
# app/scripts/blacklab/build_blacklab_security_image.sh; never built on the
# production server. run_bls_prod.sh pins the resulting image ID.
# =============================================================================

FROM instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7

ARG LIBBROTLI1_MIN_VERSION=1.1.0-2ubuntu0.1

# Upgrade only libbrotli1 (no other package) and fail the build if the
# installed version is still below the fixed one.
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade libbrotli1 \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' libbrotli1)" ge "${LIBBROTLI1_MIN_VERSION}" \
    && rm -rf /var/lib/apt/lists/*
