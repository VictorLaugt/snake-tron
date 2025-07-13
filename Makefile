IMAGE_NAME = snaketron-dev-env
DOCKERFILE_DIR = .
DOCKERFILE = $(DOCKERFILE_DIR)/Dockerfile
IMAGEBUILT = .imagebuilt


run: $(DOCKERFILE) $(IMAGEBUILT)
	sudo ./run_in_docker.sh "$(IMAGE_NAME)" "$(DOCKERFILE_DIR)"

build: $(IMAGEBUILT)

$(IMAGEBUILT): $(DOCKERFILE)
	sudo docker build -t "$(IMAGE_NAME)" "$(DOCKERFILE_DIR)"
	@touch $(IMAGEBUILT)

clean:
	@sudo docker ps -a --filter "ancestor=$(IMAGE_NAME)" --filter "status=exited" -q | xargs -r docker rm
	@sudo docker rmi $(IMAGE_NAME) 2> /dev/null || true
	@touch $(IMAGEBUILT)
	@rm $(IMAGEBUILT)

.PHONY: run build clean
