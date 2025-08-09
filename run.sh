#!/usr/bin/env bash
set -euo pipefail
cd /home/pi/Documents/Repositorios/ExoRehability || exit 1

# venv (si existe)
[ -f venv/bin/activate ] && source venv/bin/activate

# actualizar (no fallar si no hay red)
git pull origin raspberrypi5 || echo "[WARN] git pull falló, sigo local"

# prueba visual (requiere: sudo apt install feh)
feh --fullscreen /home/pi/Downloads/linux.png &

# tu app (descomenta cuando quieras)
# python3 main.py
