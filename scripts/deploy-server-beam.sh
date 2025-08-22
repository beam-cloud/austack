#!/bin/bash

INVOKE_URL=$(beam deploy deploy/beam/app.py:austack_app --format json | jq .invoke_url)
NEW_URL="${INVOKE_URL/https:\/\//wss://}"
BEAM_AUTH_TOKEN=$(beam config list --show-token | grep default | awk '{print $4}')
python scripts/setup-env.py --set BEAM_AUTH_TOKEN=$BEAM_AUTH_TOKEN --set WEBSOCKET_URL=$NEW_URL
