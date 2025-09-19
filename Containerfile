FROM scratch AS ctx
COPY /build /build

FROM ghcr.io/ublue-os/fedora-toolbox:latest

RUN --mount=type=cache,dst=/var/cache/libdnf5 \
    --mount=type=cache,dst=/var/cache/rpm-ostree \
    --mount=type=bind,from=ctx,source=/build,target=/build \
    /build/install_deps.sh
