FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/excalibur

RUN apt-get update && apt-get install -y --no-install-recommends \
    ansible \
    ca-certificates \
    git \
    nmap \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir .

RUN mkdir -p /workspace/artifacts

ENTRYPOINT ["excalibur"]
CMD ["profiles"]
