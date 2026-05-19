#!/bin/bash
set -e

# Load environment variables from .env if present
if [ -f /root/.zeroclaw/.env ]; then
    set -a
    source /root/.zeroclaw/.env
    set +a
fi

# Replace environment variables in config.toml
if [ -n "${ANTHROPIC_API_KEY}" ]; then
    sed -i "s|\${ANTHROPIC_API_KEY}|${ANTHROPIC_API_KEY}|g" /root/.zeroclaw/config.toml
fi
if [ -n "${DISCORD_BOT_TOKEN}" ]; then
    sed -i "s|\${DISCORD_BOT_TOKEN}|${DISCORD_BOT_TOKEN}|g" /root/.zeroclaw/config.toml
fi

exec "$@"
