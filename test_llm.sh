#!/bin/bash
# Test LLM endpoints before running pipeline
# Exit 0 if at least one works, Exit 1 if all fail

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing LLM Endpoints"
echo "=========================================="

# Load env vars
export $(grep -v '^#' .env | xargs) 2>/dev/null || true

DASHSCOPE_OK=false
OPENROUTER_OK=false
DEEPSEEK_OK=false

# Test 1: DashScope (Primary)
echo -n "Testing DashScope (qwen-max-latest)... "
if curl -s -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer ${DASHSCOPE_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-max-latest",
    "messages": [{"role": "user", "content": "Say DASH_OK"}],
    "max_tokens": 10
  }' \
  -m 15 2>/dev/null | grep -q "DASH_OK"; then
    echo -e "${GREEN}✓ OK${NC}"
    DASHSCOPE_OK=true
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 2: OpenRouter (Fallback 1)
echo -n "Testing OpenRouter (qwen/qwen-2.5-72b-instruct)... "
if curl -s -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen-2.5-72b-instruct",
    "messages": [{"role": "user", "content": "Say OR_OK"}],
    "max_tokens": 10
  }' \
  -m 15 2>/dev/null | grep -q "OR_OK"; then
    echo -e "${GREEN}✓ OK${NC}"
    OPENROUTER_OK=true
else
    echo -e "${RED}✗ FAIL${NC}"
fi

# Test 3: DeepSeek (Fallback 2)
echo -n "Testing DeepSeek (deepseek-chat)... "
if curl -s -X POST https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Say DS_OK"}],
    "max_tokens": 10
  }' \
  -m 15 2>/dev/null | grep -q "DS_OK"; then
    echo -e "${GREEN}✓ OK${NC}"
    DEEPSEEK_OK=true
else
    echo -e "${RED}✗ FAIL${NC}"
fi

echo "=========================================="

# Summary
if [ "$DASHSCOPE_OK" = true ] || [ "$OPENROUTER_OK" = true ] || [ "$DEEPSEEK_OK" = true ]; then
    echo -e "${GREEN}SUCCESS: At least one LLM endpoint is working${NC}"
    echo "Priority order: DashScope -> OpenRouter -> DeepSeek"
    exit 0
else
    echo -e "${RED}FAILURE: All LLM endpoints failed${NC}"
    echo "Check your API keys in .env"
    exit 1
fi
