# First stage: Build the app
FROM node:16-alpine3.15 as builder
WORKDIR /home/realtime-chat-app-react-ui

# Copy all files from local to the working directory inside the container
COPY ./ /home/realtime-chat-app-react-ui

# Set npm registry and install dependencies
RUN npm config set registry http://registry.npm.taobao.org
RUN npm install

# Build the app
RUN npm run build

# Second stage: Serve the app
FROM node:16-alpine3.15

# Set working directory for the new stage
WORKDIR /home/realtime-chat-app-react-ui

# Copy the build output from the 'builder' stage
COPY --from=builder /home/realtime-chat-app-react-ui/build /home/realtime-chat-app-react-ui

# Set npm registry and install serve package globally
RUN npm config set registry http://registry.npm.taobao.org
RUN npm install -g serve

# Command to serve the built app
CMD ["serve", "-s", "/home/realtime-chat-app-react-ui"]
