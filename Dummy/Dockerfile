# # ---- Base --------------------------------------------------------
# FROM python:3.12-slim as builder
# LABEL maintainer="Richard Wolf <richardwolf@gmail.com>"
# LABEL longevity.team="Sarah Vardy, Richard Wolf"

# ENV PYTHONUNBUFFERED=1
# ENV PYTHON=python3.12
# ENV PATH="/venv/bin:$PATH"

# # Add app user
# ARG APPLICATION_USER=user
# RUN adduser -u 1000 --disabled-password ${APPLICATION_USER}

# RUN mkdir -p /project \
#     && mkdir -p /requirements \
#     && python3 -m venv /venv \
#     && /venv/bin/python -m pip install --upgrade pip wheel \
#     && /venv/bin/python -m pip install poetry \
#     && /venv/bin/python -m pip install pandas uvicorn rich typer \
#     pydantic pyclamd python-jose boto3 botocore awscli \
#     && apt-get update -qq -y \
#     && apt-get install -qq -y libpq-dev libaio1 build-essential \
#     git bash wget curl make python3-dev \
#     && apt-get clean

# WORKDIR /project

# COPY entrypoint.sh /usr/bin/.entrypoint.sh
# RUN chmod +x /usr/bin/.entrypoint.sh

# # Copy the application code
# COPY main.py /project/
# COPY logging.conf /project/
# COPY pyproject.toml /project/
# COPY poetry.lock /project/
# COPY fedrisk_api /project/fedrisk_api
# COPY config /project/config
# COPY alembic /project/alembic
# COPY alembic.ini /project/alembic.ini
# COPY alembic/versions /project/alembic/versions
# COPY main.py /project/main.py
# COPY manage.py /project/manage.py
# COPY console_only_logging.conf logging.conf /project/
# COPY .wpg /project/.wpg
# COPY savtest /project/savtest
# COPY tests /project/tests

# RUN poetry self add poetry-plugin-export

# RUN poetry build && \
#     /venv/bin/python -m pip install --upgrade pip && \
#     poetry export -o /requirements/requirements.txt && \
#     poetry export --without-hashes -o /requirements/requirements-dev.txt --with dev && \
#     /venv/bin/python -m pip install -r /requirements/requirements.txt && \
#     /venv/bin/python -m pip install -r /requirements/requirements-dev.txt && \
#     /venv/bin/python -m pip install /project/dist/fedrisk_api-*.whl && \
#     /venv/bin/python -m pip install six

# # Install six if not already present
# # RUN pip install six

# # Patch the broken import in botocore/compat.py
# RUN sed -i 's/from botocore.vendored.six.moves import http_client/from six.moves import http_client/' $(find /venv/lib -name compat.py)

# RUN chown -R ${APPLICATION_USER}:${APPLICATION_USER} /project \
#     && chown -R ${APPLICATION_USER}:${APPLICATION_USER} /venv \
#     && chown -R ${APPLICATION_USER}:${APPLICATION_USER} /requirements

# USER ${APPLICATION_USER}

# ENTRYPOINT ["/usr/bin/.entrypoint.sh"]
# CMD ["default"]

# # ---- Hardened-Base ------------------------------------------
# FROM python:3.12-slim as hardened_base

# LABEL maintainer="Richard Wolf <richardwolf@gmail.com>"
# LABEL longevity.team="Sarah Vardy, Richard Wolf"

# ENV PYTHONUNBUFFERED=1
# ENV PYTHON=python3.12
# ENV PATH="/venv/bin:$PATH"

# WORKDIR /project

# # Add app user
# ARG APPLICATION_USER=user
# RUN adduser -u 1000 --disabled-password ${APPLICATION_USER}

# COPY entrypoint.sh /usr/bin/.entrypoint.sh
# RUN chmod +x /usr/bin/.entrypoint.sh

# ENTRYPOINT ["/usr/bin/.entrypoint.sh"]
# CMD ["default"]

# # ---- Final --------------------------------------------------------
# FROM hardened_base as final
# LABEL maintainer="Richard Wolf"

# ENV PYTHONUNBUFFERED=1
# ENV PYTHON=python3.12
# ENV PATH="/venv/bin:$PATH"

# RUN apt-get update && \
#     apt-get install -y libpq5 tzdata && \
#     ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime && \
#     dpkg-reconfigure -f noninteractive tzdata && \
#     apt-get clean

# COPY --from=builder /project/pyproject.toml \
#     /project/poetry.lock \
#     /project/main.py \
#     /project/alembic.ini \
#     /project/console_only_logging.conf \
#     /project/logging.conf \
#     /project/manage.py /project/
# COPY --from=builder /project/config /project/config/
# COPY --from=builder /project/alembic /project/alembic/
# COPY --from=builder /project/tests /project/tests
# COPY --from=builder /project/savtest /project/savtest
# COPY --from=builder /venv /venv

# # Add docker-compose-wait tool -------------------
# ENV WAIT_VERSION=2.7.2
# ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
# RUN chmod +x /wait

# CMD ["/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# USER user

# # ---- Test --------------------------------------------------------------
# FROM builder as test
# LABEL maintainer="Richard Wolf <rwolf@cisco.com>"

# ENV PYTHONUNBUFFERED=1

# RUN /venv/bin/python -m pip install -r /requirements/requirements-dev.txt

# COPY --from=builder /project/.wpg /project/.wpg
# COPY --from=builder /project/config /project/config
# COPY --from=builder /project/tests /project/tests
# COPY --from=builder /project/savtest /project/savtest

# RUN chown -R user:user /project

# USER user

# CMD ["pytest"]

# # ---- Development -------------------------------------------------------
# FROM builder as develop
# LABEL maintainer="Richard Wolf <rwolf@cisco.com>"

# ENV PYTHONUNBUFFERED=1

# COPY --from=test /venv /venv

# USER root

# ENV WAIT_VERSION=2.7.2
# ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
# RUN chmod +x /wait

# USER user

# ---- Base --------------------------------------------------------
FROM python:3.12-alpine as builder

LABEL maintainer="Richard Wolf <richardwolf@gmail.com>"
LABEL longevity.team="Sarah Vardy, Richard Wolf"

ENV PYTHONUNBUFFERED=1
ENV PYTHON=python3.12
ENV PATH="/venv/bin:$PATH"

# Add app user
ARG APPLICATION_USER=user
RUN adduser -u 1000 -D ${APPLICATION_USER}

RUN apk add --no-cache \
        build-base \
        gcc \
        git \
        bash \
        curl \
        make \
        libffi-dev \
        musl-dev \
        openssl-dev \
        postgresql-dev \
        python3-dev \
        libaio \
        tzdata \
    && python3 -m venv /venv \
    && /venv/bin/pip install --upgrade pip wheel \
    && /venv/bin/pip install poetry \
    && /venv/bin/pip install pandas uvicorn rich typer \
        pydantic pyclamd python-jose boto3 botocore awscli

WORKDIR /project

COPY entrypoint.sh /usr/bin/.entrypoint.sh
RUN chmod +x /usr/bin/.entrypoint.sh

COPY main.py /project/
COPY logging.conf /project/
COPY pyproject.toml poetry.lock /project/
COPY fedrisk_api /project/fedrisk_api
COPY config /project/config
COPY alembic /project/alembic
COPY alembic.ini /project/alembic.ini
COPY alembic/versions /project/alembic/versions
COPY manage.py /project/manage.py
COPY console_only_logging.conf logging.conf /project/
COPY .wpg /project/.wpg
COPY savtest /project/savtest
COPY tests /project/tests

RUN poetry self add poetry-plugin-export && \
    poetry build && \
    poetry export --without-hashes -o /requirements.txt && \
    poetry export --without-hashes -o /requirements-dev.txt --with dev && \
    /venv/bin/pip install -r /requirements.txt && \
    /venv/bin/pip install -r /requirements-dev.txt && \
    /venv/bin/pip install /project/dist/fedrisk_api-*.whl && \
    /venv/bin/pip install six

# Patch botocore for six compatibility
RUN sed -i 's/from botocore.vendored.six.moves import http_client/from six.moves import http_client/' $(find /venv/lib -name compat.py)

RUN chown -R ${APPLICATION_USER}:${APPLICATION_USER} /project /venv

USER ${APPLICATION_USER}

ENTRYPOINT ["/usr/bin/.entrypoint.sh"]
CMD ["default"]

# ---- Hardened-Base ------------------------------------------
FROM python:3.12-alpine as hardened_base

LABEL maintainer="Richard Wolf <richardwolf@gmail.com>"
LABEL longevity.team="Sarah Vardy, Richard Wolf"

ENV PYTHONUNBUFFERED=1
ENV PYTHON=python3.12
ENV PATH="/venv/bin:$PATH"

WORKDIR /project

ARG APPLICATION_USER=user
RUN adduser -u 1000 -D ${APPLICATION_USER}

COPY entrypoint.sh /usr/bin/.entrypoint.sh
RUN chmod +x /usr/bin/.entrypoint.sh

ENTRYPOINT ["/usr/bin/.entrypoint.sh"]
CMD ["default"]

# ---- Final --------------------------------------------------------
FROM hardened_base as final
LABEL maintainer="Richard Wolf"

ENV PYTHONUNBUFFERED=1
ENV PYTHON=python3.12
ENV PATH="/venv/bin:$PATH"

RUN apk add --no-cache libpq tzdata && \
    cp /usr/share/zoneinfo/America/New_York /etc/localtime && \
    echo "America/New_York" > /etc/timezone

COPY --from=builder /project /project
COPY --from=builder /venv /venv

# Add docker-compose-wait
ENV WAIT_VERSION=2.7.2
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait

CMD ["/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

USER user

# ---- Test --------------------------------------------------------
FROM builder as test
LABEL maintainer="Richard Wolf <rwolf@cisco.com>"

RUN /venv/bin/pip install -r /requirements-dev.txt
USER user
CMD ["pytest"]

# ---- Development --------------------------------------------------------
FROM builder as develop
LABEL maintainer="Richard Wolf <rwolf@cisco.com>"

COPY --from=test /venv /venv

USER root
ENV WAIT_VERSION=2.7.2
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait

USER user