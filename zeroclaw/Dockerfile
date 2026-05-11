# ZeroClaw Dockerfile
FROM rust:1.88-slim as rust-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and build ZeroClaw
RUN git clone https://github.com/zeroclaw-labs/zeroclaw.git .
RUN cargo build --release

# Web builder stage
FROM node:20-slim as web-builder

WORKDIR /app

# Install git, curl, and build dependencies
RUN apt-get update && apt-get install -y git curl pkg-config libssl-dev build-essential && rm -rf /var/lib/apt/lists/*

# Clone zeroclaw for web files
RUN git clone https://github.com/zeroclaw-labs/zeroclaw.git .

# Install cargo for xtask
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Build xtask binary first
RUN cargo build -p xtask

# Build web dashboard with API generation using the built xtask
RUN cargo run -p xtask --bin web -- build

# Runtime image
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copy ZeroClaw binary
COPY --from=rust-builder /app/target/release/zeroclaw /usr/local/bin/zeroclaw

# Copy web dist files
COPY --from=web-builder /app/web/dist /app/web/dist

# Create config directory
RUN mkdir -p /root/.zeroclaw

# Copy default config
COPY config.toml /root/.zeroclaw/config.toml

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ZeroClaw ports (if needed for channels)
EXPOSE 8080

# Run ZeroClaw with entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["zeroclaw", "gateway"]
