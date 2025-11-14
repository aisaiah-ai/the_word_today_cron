#!/bin/bash

# Script to monitor deployments and report errors

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Monitoring All Deployments                                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check daily-readings-seeder-secondary
echo "1. Checking daily-readings-seeder-secondary..."
DAILY_RUN=$(gh run list --repo aisaiah-ai/the_word_today_cron \
  --workflow="Deploy Daily Readings Seeder (Secondary Firebase)" \
  --limit=1 --json databaseId,status,conclusion --jq '.[0]')

if [ -n "$DAILY_RUN" ] && [ "$DAILY_RUN" != "null" ]; then
  DAILY_ID=$(echo "$DAILY_RUN" | jq -r '.databaseId')
  DAILY_STATUS=$(echo "$DAILY_RUN" | jq -r '.status')
  DAILY_CONCLUSION=$(echo "$DAILY_RUN" | jq -r '.conclusion // "in progress"')
  
  echo "   Status: $DAILY_STATUS"
  echo "   Conclusion: $DAILY_CONCLUSION"
  
  if [ "$DAILY_CONCLUSION" = "failure" ]; then
    echo "   ❌ FAILED - Checking errors..."
    gh run view $DAILY_ID --repo aisaiah-ai/the_word_today_cron --log 2>&1 | \
      grep -E "ERROR|FAILED|Error" | tail -10
  fi
else
  echo "   ⚠️ No runs found"
fi

echo ""

# Check the-word-today-cron-secondary
echo "2. Checking the-word-today-cron-secondary..."
WORD_RUN=$(gh run list --repo aisaiah-ai/the_word_today_cron \
  --workflow="Deploy The Word Today Cron (Secondary Firebase)" \
  --limit=1 --json databaseId,status,conclusion --jq '.[0]')

if [ -n "$WORD_RUN" ] && [ "$WORD_RUN" != "null" ]; then
  WORD_ID=$(echo "$WORD_RUN" | jq -r '.databaseId')
  WORD_STATUS=$(echo "$WORD_RUN" | jq -r '.status')
  WORD_CONCLUSION=$(echo "$WORD_RUN" | jq -r '.conclusion // "in progress"')
  
  echo "   Status: $WORD_STATUS"
  echo "   Conclusion: $WORD_CONCLUSION"
  
  if [ "$WORD_CONCLUSION" = "failure" ]; then
    echo "   ❌ FAILED - Checking errors..."
    gh run view $WORD_ID --repo aisaiah-ai/the_word_today_cron --log 2>&1 | \
      grep -E "ERROR|FAILED|Error" | tail -10
  fi
else
  echo "   ⚠️ No runs found"
fi

echo ""
echo "View all runs: https://github.com/aisaiah-ai/the_word_today_cron/actions"

