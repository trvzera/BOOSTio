FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home botio \
    && mkdir /data && chown botio:botio /data
COPY main.py policy.py welcome.py commands.py movement.py member_count.py tickets.py ./
USER 10001:10001
CMD ["python", "main.py"]
