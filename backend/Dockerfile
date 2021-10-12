# pull the official base image
FROM python:3.8.12-bullseye

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /usr/src/app

# install dependencies
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt install -y netcat
COPY /requirements.txt /usr/src/app
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
