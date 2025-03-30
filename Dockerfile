FROM python:3.11-slim


ENV PATH=$PATH:/dutyproject \
    PDM_VERSION="2.22.4" 

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /dutyproject

# Install cron
RUN apt-get update && apt-get install -y cron

COPY pyproject.toml pdm.lock* ./

RUN pip install pdm==$PDM_VERSION && pdm config python.use_venv False \
    && pdm install -p /dutyproject -g --no-editable --no-self --check -v

COPY . /dutyproject/

EXPOSE 8000

ENTRYPOINT ["pdm", "run"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
