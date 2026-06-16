FROM linuxserver/blender:4.1.1

WORKDIR /app

COPY requirements.txt .

RUN python3 -m ensurepip --upgrade || true
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}