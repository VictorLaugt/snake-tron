IMAGENAME = snaketron-dev-env
DOCKERFILE_DIR = .
DOCKERFILE = $(DOCKERFILE_DIR)/Dockerfile
IMAGEBUILT = .imagebuilt


run: $(DOCKERFILE) $(IMAGEBUILT)
	@echo "Running the app in a container using image: $(IMAGENAME)" && \
	xhost +local:docker && \
	trap 'xhost -local:docker' INT TERM EXIT && \
	sudo docker run --rm -it \
		-e DISPLAY=$$DISPLAY \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		"$(IMAGENAME)"

build: $(IMAGEBUILT)

$(IMAGEBUILT): $(DOCKERFILE)
	@echo "Building image: $(IMAGENAME)"
	@sudo docker build -t "$(IMAGENAME)" "$(DOCKERFILE_DIR)"
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
