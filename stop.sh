#!/bin/bash
# Stop COGNET LDI Engine
echo "Stopping COGNET LDI Engine..."

if [ -f /tmp/cognet_api.pid ]; then
    kill $(cat /tmp/cognet_api.pid) 2>/dev/null && echo "  ✓ API stopped" || echo "  - API not running"
    rm -f /tmp/cognet_api.pid
fi

if [ -f /tmp/cognet_admin.pid ]; then
    kill $(cat /tmp/cognet_admin.pid) 2>/dev/null && echo "  ✓ Admin stopped" || echo "  - Admin not running"
    rm -f /tmp/cognet_admin.pid
fi

# Cleanup any remaining processes on our ports
lsof -ti:8000 2>/dev/null | xargs kill 2>/dev/null || true
lsof -ti:3000 2>/dev/null | xargs kill 2>/dev/null || true

echo "Done."
