# Use the official Node.js image as the base

FROM node:18.16-alpine3.17

# Set the working directory in the container

WORKDIR /home/sample-app

RUN mkdir -p /home/sample-app
# Copy package.json and package-lock.json

COPY ./client/package*.json ./

# Install dependencies

RUN npm install

# Copy the rest of the application code

COPY ./client ./

# Expose the port your app listens on

EXPOSE 3000

# Start the Node.js application

CMD [ "npm", "start" ]