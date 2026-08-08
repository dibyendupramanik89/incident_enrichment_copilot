FROM python:3.12-slim
WORKDIR /workspace
# Copy entire repository into the image to preserve relative paths used by modules
COPY . /workspace
RUN pip install --no-cache-dir -r /workspace/requirements.txt
WORKDIR /workspace/apps/backend
EXPOSE 8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
