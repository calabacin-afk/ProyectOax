FROM postgis/postgis:17-3.5

ARG PG_MAJOR=17
ARG PGVECTOR_VERSION=v0.8.7

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git \
        postgresql-server-dev-${PG_MAJOR} \
    && git clone --depth 1 --branch ${PGVECTOR_VERSION} \
        https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && make OPTFLAGS="" -C /tmp/pgvector \
    && make -C /tmp/pgvector install \
    && rm -rf /tmp/pgvector \
    && apt-get purge -y --auto-remove \
        build-essential \
        git \
        postgresql-server-dev-${PG_MAJOR} \
    && rm -rf /var/lib/apt/lists/*
