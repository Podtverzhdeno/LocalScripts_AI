FROM python:3.11-slim

# Install Lua
RUN apt-get update && apt-get install -y lua5.4 luac && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run with task from env
ENV TASK="write a fibonacci function in Lua"
ENV LLM_BACKEND=openai

CMD ["python", "main.py", "--task", "${TASK}"]
