FROM harbor.10.0.0.200.nip.io/library/postgresql:18.4.0 AS builder
USER root
RUN install_packages curl build-essential 2>/dev/null || \
    (apt-get update -qq && apt-get install -y --no-install-recommends curl build-essential)
RUN curl -fsSL https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.4.tar.gz | tar xz -C /tmp
# Recompile pgvector without AVX-512 SIMD instructions.
# The upstream Bitnami build includes EVEX-encoded (AVX-512) paths that crash (SIGILL)
# on i7-8565U and i7-10510U CPUs (Whiskey Lake / Comet Lake — no AVX-512 support).
# -mno-avx512* forces GCC to use only SSE4/AVX2 code paths.
RUN cd /tmp/pgvector-0.8.4 && \
    make OPTFLAGS="-mno-avx512f -mno-avx512bw -mno-avx512vl -mno-avx512dq" \
         PG_CONFIG=/opt/bitnami/postgresql/bin/pg_config && \
    cp vector.so /tmp/vector-nosimd.so

FROM harbor.10.0.0.200.nip.io/library/postgresql:18.4.0
COPY --from=builder /tmp/vector-nosimd.so /opt/bitnami/postgresql/lib/vector.so
