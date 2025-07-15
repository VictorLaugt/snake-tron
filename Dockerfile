FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    libxcursor-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxi-dev \
    libudev-dev \
    libmtdev-dev \
    libffi-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app

RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt

CMD python snaketron; bash
# CMD ["python", "snaketron"]
