FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*

RUN pip install asyncssh==2.14.2

COPY server.py .

# Generate SSH host key
RUN ssh-keygen -t rsa -f /tmp/ssh_host_key -N ''

EXPOSE 2222

CMD ["python", "server.py"]
