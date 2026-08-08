#!/usr/bin/env bash
# scripts/health_check.sh — curl every service's /health endpoint
set -e
for entry in "alarm-api:8000" "alarm-mcp:9000" "ticketing-mcp:9001" "backend:8080"; do
  name="${entry%%:*}"
  port="${entry##*:}"
  echo -n "$name (:$port) -> "
  curl -s -m 5 "http://localhost:$port/health" || echo "UNREACHABLE"
  echo
done
