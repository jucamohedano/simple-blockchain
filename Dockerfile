FROM python:3.6-alpine

WORKDIR /app

# Install dependencies.
ADD requirements.txt /app
RUN pip install -r requirements.txt

# Add actual source code.
ADD blockchain.py /app
ADD register_pods.py /app

# deps
RUN apk add curl

EXPOSE 5000

CMD ["python", "blockchain.py", "--port", "5000"] 
