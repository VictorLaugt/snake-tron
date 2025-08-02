CONTEXT_DIR = .
DOCKERFILE = $(CONTEXT_DIR)/Dockerfile
SOURCE_DIR = $(CONTEXT_DIR)/snaketron
IMAGENAME = snaketron-dev-env
IMAGEBUILT = .imagebuilt  # file to indicate that the docker image has been built

run: $(DOCKERFILE) $(IMAGEBUILT)
	@echo "Running the app in a container using image: $(IMAGENAME)" && \
	xhost +local:docker && \
	trap 'xhost -local:docker' INT TERM EXIT && \
	sudo docker run --rm -it \
		-e DISPLAY=$$DISPLAY \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		-v "$(realpath $(SOURCE_DIR)):/app/snaketron" \
		"$(IMAGENAME)"

build: $(IMAGEBUILT)

$(IMAGEBUILT): $(DOCKERFILE)
	@echo "Building image: $(IMAGENAME)"
	@sudo docker build -t "$(IMAGENAME)" "$(CONTEXT_DIR)"
	@echo $(IMAGENAME) > $(IMAGEBUILT)

clean:
	@touch $(IMAGEBUILT)
	@while IFS= read -r image; do \
		echo "Removing containers using image: $$image"; \
		sudo docker ps -aq --filter ancestor=$$image | xargs -r sudo docker rm -f; \
		echo "Removing image: $$image"; \
		sudo docker rmi -f $$image || true; \
	done < $(IMAGEBUILT);
	@rm $(IMAGEBUILT)

.PHONY: run build clean
