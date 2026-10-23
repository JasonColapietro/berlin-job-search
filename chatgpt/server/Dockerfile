FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
COPY chatgpt/server/requirements.txt /app/chatgpt/server/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/chatgpt/server/requirements.txt

COPY chatgpt/__init__.py /app/chatgpt/__init__.py
COPY chatgpt/server /app/chatgpt/server
COPY chatgpt/STARTER-PROMPT.md /app/chatgpt/STARTER-PROMPT.md
COPY skills/berlin-job-search/scripts/search.py /app/skills/berlin-job-search/scripts/search.py
COPY skills/berlin-job-search/scripts/analyze_jd.py /app/skills/berlin-job-search/scripts/analyze_jd.py
COPY skills/berlin-job-search/scripts/job_detail.py /app/skills/berlin-job-search/scripts/job_detail.py
COPY skills/berlin-job-search/assets/companies.json /app/skills/berlin-job-search/assets/companies.json

RUN chown -R app:app /app
USER app

CMD ["uvicorn", "chatgpt.server.app:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
