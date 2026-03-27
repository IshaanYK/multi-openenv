FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Run on port 7860 for Hugging Face Spaces
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
