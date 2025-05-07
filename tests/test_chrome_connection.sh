#!/usr/bin/env bash

echo "Testing Chrome remote debugging connection..."
curl -s http://localhost:9222/json | python -m json.tool