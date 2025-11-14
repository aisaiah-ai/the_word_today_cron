#!/bin/bash
# Check secondary seeder status and trigger if needed

echo "Checking secondary daily readings seeder..."

# The function should seed based on the current date
# Let's trigger it manually for today's date range

TODAY=$(date +%Y-%m-%d)
CURRENT_MONTH=$(date +%Y-%m)
FIRST_DAY="${CURRENT_MONTH}-01"
LAST_DAY=$(date -d "$(date +%Y-%m-01) +1 month -1 day" +%Y-%m-%d 2>/dev/null || date -v1d -v+1m -v-1d +%Y-%m-%d 2>/dev/null || echo "${CURRENT_MONTH}-30")

echo "Current date: $TODAY"
echo "Seeding range: $FIRST_DAY to $LAST_DAY"
echo ""
echo "To trigger manually, use the workflow:"
echo "gh workflow run 'Trigger Secondary Seeder (Workload Identity)' \\"
echo "  -f start_date=$FIRST_DAY \\"
echo "  -f end_date=$LAST_DAY"

