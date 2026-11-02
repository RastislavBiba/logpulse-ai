# 1. Použijeme oficiálny ľahký Python obraz namiesto čistého Ubuntu
FROM python:3.11-slim

# 2. Nastavenie Pythonu pre kontajnery (okamžité logovanie bez vyrovnávacej pamäte)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 3. Skopírovanie a inštalácia knižníc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Skopírovanie zvyšku kódu (main.py atď.)
COPY . .

# 5. Otvorenie portu
EXPOSE 8000

# 6. Spustenie FastAPI servera cez uvicorn na 0.0.0.0
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
