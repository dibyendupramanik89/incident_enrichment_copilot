FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/frontend/app.py /app/
EXPOSE 7860
CMD ["python", "app.py"]
