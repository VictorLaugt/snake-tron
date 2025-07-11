IMAGE_NAME = snaketron-dev-env
DOCKERFILE_DIR = .

run:
	sudo ./run_in_docker.sh "$(IMAGE_NAME)" "$(DOCKERFILE_DIR)"

clean:
	@sudo docker ps -a --filter "ancestor=$(IMAGE_NAME)" --filter "status=exited" -q | xargs -r docker rm
	@sudo docker rmi $(IMAGE_NAME) 2> /dev/null || true
