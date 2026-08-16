FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, data (for indexes), and create monitoring folder
COPY backend/ ./backend/
COPY data/ ./data/
RUN mkdir -p monitoring

# We expose 8000 for FastAPI and 8501 for Streamlit
EXPOSE 8000 8501
