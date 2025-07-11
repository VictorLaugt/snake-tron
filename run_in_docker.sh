#!/bin/bash
set -e

IMAGE_NAME="$1"
DOCKERFILE_DIR="$2"

if [ -z "$IMAGE_NAME" ] || [ -z "$DOCKERFILE_DIR" ]; then
    echo "usage: $0 image_name dockerfile_dir"
    exit 1
fi

# IMAGE_NAME='snaketron-dev-env'
# DOCKERFILE_DIR='.'

if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Image $IMAGE_NAME not found"
    echo "Creating the image"
    docker build -t "$IMAGE_NAME" "$DOCKERFILE_DIR"
else
    echo "Image $IMAGE_NAME found"
fi

# Allow local Docker connections to the X server while the container is running
xhost +local:docker
trap 'xhost -local:docker' INT TERM EXIT

echo "Running the app"

# Run container with shared X11 display
docker run --rm -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  "$IMAGE_NAME"
