FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TZ=Asia/Kathmandu

ENTRYPOINT ["python", "main.py"]
CMD ["--schedule"]
