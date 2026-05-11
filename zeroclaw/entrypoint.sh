#!/bin/bash
# Replace environment variables in config.toml
sed -i "s/\${ANTHROPIC_API_KEY}/${ANTHROPIC_API_KEY}/g" /root/.zeroclaw/config.toml
sed -i "s/\${DISCORD_BOT_TOKEN}/${DISCORD_BOT_TOKEN}/g" /root/.zeroclaw/config.toml
exec "$@"
