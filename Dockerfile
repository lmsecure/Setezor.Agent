FROM python:3.13-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
WORKDIR /app
COPY setezor/requirements.txt .
RUN python3 -m pip install --prefix=/install --no-cache-dir --root-user-action=ignore -r requirements.txt
COPY setezor setezor

FROM python:3.13-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
      nmap \
      masscan \
      libasound2 \
      libatk-bridge2.0-0 \
      libatk1.0-0 \
      libatspi2.0-0 \
      libcairo2 \
      libcups2 \
      libdbus-1-3 \
      libdrm2 \
      libgbm1 \
      libglib2.0-0 \
      libnspr4 \
      libnss3 \
      libpango-1.0-0 \
      libx11-6 \
      libxcb1 \
      libxcomposite1 \
      libxdamage1 \
      libxext6 \
      libxfixes3 \
      libxkbcommon0 \
      libxrandr2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /app /app
CMD ["python3", "setezor/agent.py"]
