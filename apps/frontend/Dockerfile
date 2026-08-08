FROM python:3.12-slim
WORKDIR /workspace
COPY . /workspace
RUN pip install --no-cache-dir -r /workspace/requirements.txt
WORKDIR /workspace/apps/frontend
EXPOSE 7860
CMD ["python", "app.py"]
