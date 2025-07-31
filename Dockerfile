FROM python:3.12.7

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5200

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5200", "--reload"]