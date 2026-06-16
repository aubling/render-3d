# Blender build v4
FROM linuxserver/blender:4.1.1

WORKDIR /app

COPY requirements.txt .

RUN rm -f /etc/apt/sources.list.d/nodesource.list \
    && rm -f /etc/apt/sources.list.d/*node* \
    && apt-get update \
    && apt-get install -y python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}