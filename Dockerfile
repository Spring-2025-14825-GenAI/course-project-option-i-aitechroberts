FROM python:3.10
WORKDIR /app
COPY /documents /documents
COPY nih_key.json nih_key.json
COPY .env .env
COPY requirements.txt requirements.txt
COPY app.py app.py
RUN pip install -r requirements.txt
EXPOSE 8080
CMD streamlit run --server.port 8080 --server.enableCORS false app.py 