FROM 3.9.23-alpine3.21

# Create app directory
ENV APP_HOME /usr/src/app
WORKDIR $APP_HOME

# Install app dependencies
COPY requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r ./requirements.txt && rm ./requirements.txt

# Copy source code
COPY . ./
RUN chmod +x ./*.sh

ENTRYPOINT ["sh", "-c"]
CMD [ "./execute.sh" ]
