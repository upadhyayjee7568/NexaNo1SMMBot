#!/usr/bin/env bash
set -euo pipefail

python -c "from app.bot.runtime import run_polling; run_polling()"
