FROM python:3.7.0
COPY app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD gunicorn -b :5000 app:app
EXPOSE 5000

