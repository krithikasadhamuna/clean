#!/bin/bash
# Test simulation API on production server
# This will show you the EXACT response the frontend is receiving

echo "=========================================="
echo "Testing Simulation API"
echo "=========================================="
echo ""

# Test 1: Check if endpoint accepts GET
echo "[TEST 1] Testing GET request..."
echo "URL: http://backend.codegrey.ai:8080/api/backend/gpt-scenarios/execute?scenario_id=real_system_compromise"
echo ""
curl -s -w "\nHTTP Status: %{http_code}\n" \
  "http://backend.codegrey.ai:8080/api/backend/gpt-scenarios/execute?scenario_id=real_system_compromise" \
  | jq . 2>/dev/null || cat
echo ""
echo "=========================================="
echo ""

# Test 2: Check if endpoint accepts POST
echo "[TEST 2] Testing POST request..."
echo "URL: http://backend.codegrey.ai:8080/api/backend/gpt-scenarios/execute"
echo "Body: {\"scenario_id\": \"real_system_compromise\"}"
echo ""
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "real_system_compromise"}' \
  "http://backend.codegrey.ai:8080/api/backend/gpt-scenarios/execute" \
  | jq . 2>/dev/null || cat
echo ""
echo "=========================================="
echo ""

# Test 3: Check recent server logs for errors
echo "[TEST 3] Recent server logs (last 30 lines)..."
echo ""
ssh krithika@backend.codegrey.ai "tail -30 /home/krithika/full-func/clean/server.log | grep -E '(execute|scenario|ERROR|error|failed|Failed)'" || \
ssh krithika@backend.codegrey.ai "tail -30 /home/krithika/full-func/clean/server.log"
echo ""
echo "=========================================="

