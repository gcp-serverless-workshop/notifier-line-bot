FROM python:3.9

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# Install manually all the missing libraries
RUN apt-get update
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils

# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install


WORKDIR /app
COPY . /app
EXPOSE 8080
CMD uvicorn main:app --host=0.0.0.0 --port=$PORT
