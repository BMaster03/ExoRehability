#!/usr/bin/env bash
# =======================================
# Script de inicio automático RaspberryPi5 - ExoRehability
# =======================================

# 1. Ruta de trabajo
cd /home/pi/Documents/Repositorios/ExoRehability || exit

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Actualizar repo
git pull origin raspberrypi5

# 4. Registrar inicio en log
echo "[$(date)] Script run.sh ejecutado al inicio" >> /home/pi/run_exo.log

# 5. Mostrar imagen como prueba (requiere feh instalado: sudo apt install feh)
feh --fullscreen /usr/share/rpd-wallpaper/road.jpg &

# 6. Ejecutar código principal
# python3 main.py
