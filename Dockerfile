# Imagen para desplegar la app con LibreOffice disponible — necesario
# para que el módulo de Actas genere el PDF a partir del .docx real
# (no una reconstrucción visual). Los hostings administrados tipo
# Railway/Render/Heroku no traen LibreOffice por defecto vía buildpack,
# así que este Dockerfile lo instala explícitamente.
#
# Si tu plataforma detecta este Dockerfile automáticamente (Railway lo
# hace por defecto), no hace falta nada más. Si usás Render u otro
# hosting que requiere elegir el entorno "Docker" a mano en el panel,
# recordá cambiarlo ahí — si no, va a seguir usando el buildpack de
# Python de siempre y el módulo de Actas va a fallar con "LibreOffice no
# está instalado en este servidor".

FROM python:3.11-slim

# libreoffice-writer trae los filtros para abrir/convertir .docx — instalar
# solo ese componente (no el paquete "libreoffice" completo) para no
# arrastrar Calc/Impress/Base y mantener la imagen más liviana.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend ./Backend
COPY Frontend ./Frontend

WORKDIR /app/Backend

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips=*"]
