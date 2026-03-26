#!/bin/bash
# ============================================
# COGNET LDI Engine — Start Everything
# ============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/node/bin:$PATH:/usr/bin:/bin"

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   COGNET Learning Demand Intelligence Engine ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if DB exists, if not initialize
if [ ! -f "$SCRIPT_DIR/apps/api/cognet_ldi.db" ]; then
    echo -e "${YELLOW}→ First run: Initializing database...${NC}"
    cd "$SCRIPT_DIR/apps/api"
    PYTHONPATH="$(pwd):$(pwd)/../../services:$(pwd)/../.." python3 init_db.py 2>&1 | grep -v "sqlalchemy.engine" || true
    echo ""
fi

# Check if node_modules exist for admin
if [ ! -d "$SCRIPT_DIR/apps/admin/node_modules" ]; then
    echo -e "${YELLOW}→ First run: Installing admin dependencies...${NC}"
    cd "$SCRIPT_DIR/apps/admin"
    npm install --silent 2>&1
    echo ""
fi

# Build admin if .next doesn't exist
if [ ! -d "$SCRIPT_DIR/apps/admin/.next" ]; then
    echo -e "${YELLOW}→ Building admin UI...${NC}"
    cd "$SCRIPT_DIR/apps/admin"
    npx next build 2>&1 | grep -E "(Route|✓|Compil)" || true
    echo ""
fi

# Kill any existing processes on our ports
lsof -ti:8000 2>/dev/null | xargs kill 2>/dev/null || true
lsof -ti:3000 2>/dev/null | xargs kill 2>/dev/null || true
sleep 1

# Start API
echo -e "${GREEN}→ Starting API server (port 8000)...${NC}"
cd "$SCRIPT_DIR/apps/api"
PYTHONPATH="$(pwd):$(pwd)/../../services:$(pwd)/../.." python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/cognet_api.log 2>&1 &
API_PID=$!

sleep 2

# Start Admin
echo -e "${GREEN}→ Starting Admin UI (port 3000)...${NC}"
cd "$SCRIPT_DIR/apps/admin"
npx next start -p 3000 > /tmp/cognet_admin.log 2>&1 &
ADMIN_PID=$!

sleep 2

# Verify
API_STATUS=$(curl -s http://localhost:8000/health 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','FAIL'))" 2>/dev/null || echo "FAIL")
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/en 2>/dev/null || echo "000")

echo ""
echo "  ┌──────────────────────────────────────────────┐"
echo "  │           COGNET LDI Engine                   │"
echo "  ├──────────────────────────────────────────────┤"

if [ "$API_STATUS" = "ok" ]; then
    echo -e "  │  API:        ${GREEN}http://localhost:8000${NC}        ✓  │"
    echo -e "  │  API Docs:   ${GREEN}http://localhost:8000/docs${NC}   ✓  │"
else
    echo "  │  API:        http://localhost:8000        ✗  │"
fi

if [ "$ADMIN_STATUS" = "200" ] || [ "$ADMIN_STATUS" = "307" ]; then
    echo -e "  │  Admin (EN): ${GREEN}http://localhost:3000/en${NC}     ✓  │"
    echo -e "  │  Admin (HE): ${GREEN}http://localhost:3000/he${NC}     ✓  │"
else
    echo "  │  Admin:      http://localhost:3000        ✗  │"
fi

echo "  ├──────────────────────────────────────────────┤"
echo "  │  API PID:    $API_PID                              │"
echo "  │  Admin PID:  $ADMIN_PID                              │"
echo "  ├──────────────────────────────────────────────┤"
echo "  │  Logs: /tmp/cognet_api.log                   │"
echo "  │        /tmp/cognet_admin.log                 │"
echo "  └──────────────────────────────────────────────┘"
echo ""
echo "  To stop:  kill $API_PID $ADMIN_PID"
echo ""

# Save PIDs for stop script
echo "$API_PID" > /tmp/cognet_api.pid
echo "$ADMIN_PID" > /tmp/cognet_admin.pid
