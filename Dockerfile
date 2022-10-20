#FROM selenium/node-chrome:4.0.0-alpha-7-prerelease-20201009
FROM python

USER 0

WORKDIR /usr/src/app
ENV PYTHONPATH=.

RUN apt update && apt install -y python3 python3-pip
RUN apt-get install -y libnss3 libgconf-2-4 chromium-driver

# Set the Chrome repo.
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
# Install Chrome.
RUN apt-get update && apt-get -y install google-chrome-unstable && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ADD ./credentials /root/.aws/credentials

CMD tail -f /dev/null
