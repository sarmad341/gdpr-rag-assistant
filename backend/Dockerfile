FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy backend, data (for indexes), and create monitoring folder
COPY backend/ ./backend/

RUN mkdir -p monitoring

# We expose 8000 for FastAPI and 8501 for Streamlit
EXPOSE 8000 8501
