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

debug: $(DOCKERFILE) $(IMAGEBUILT)
	@echo "Running a container using image: $(IMAGENAME)" && \
	xhost +local:docker && \
	trap 'xhost -local:docker' INT TERM EXIT && \
	sudo docker run --rm -it \
		-e DISPLAY=$$DISPLAY \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		-v "$(realpath $(SOURCE_DIR)):/app/snaketron" \
		"$(IMAGENAME)" \
		bash

build: $(IMAGEBUILT)

$(IMAGEBUILT): $(DOCKERFILE)
	@echo "Building image: $(IMAGENAME)"
	@sudo bash -c 'docker build \
		-t "$(IMAGENAME)" "$(CONTEXT_DIR)" \
		--build-arg UID=$$SUDO_UID --build-arg GID=$$SUDO_GID'
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

	@echo "Removing python app cache"
	@find . -mindepth 1 -type d -name __pycache__ -exec rm -r {} +

.PHONY: run build clean
