FROM linuxserver/blender:4.1.1
USER root
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY main.py .
COPY blender_renderer.py .
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
