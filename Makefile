CONTEXT_DIR = .
CONTAINER_FILE = $(CONTEXT_DIR)/Containerfile
SOURCE_DIR = $(CONTEXT_DIR)/snaketron
CONTAINER_APP_DIR = /app/snaketron
IMAGE_NAME = snaketron-dev-env
IMAGE_BUILT = .imagebuilt  # file to indicate that the docker image has been built

# Build display arguments
CONTAINER_ENV_ARGS = -e DISPLAY=$(DISPLAY) -v /tmp/.X11-unix:/tmp/.X11-unix:ro

# Support for Wayland
ifneq ($(WAYLAND_DISPLAY),)
	CONTAINER_ENV_ARGS += -e WAYLAND_DISPLAY=$(WAYLAND_DISPLAY) \
		-e XDG_RUNTIME_DIR=/tmp \
		-v $(XDG_RUNTIME_DIR)/$(WAYLAND_DISPLAY):/tmp/$(WAYLAND_DISPLAY):ro
endif

# Support for GPU
ifneq ($(wildcard /dev/dri),)
	CONTAINER_ENV_ARGS += --device /dev/dri:/dev/dri
endif

# Support for multitouch input device
ifneq ($(wildcard /dev/input),)
	CONTAINER_ENV_ARGS += --device /dev/input:/dev/input
endif

# Pass host groups (render + input + video) to grant access to GPUs & input devices
CONTAINER_ENV_ARGS += --group-add keep-groups

run: $(CONTAINER_FILE) $(IMAGE_BUILT)
	@echo "Running $(IMAGE_NAME) with Podman..."
	@podman run --rm -it \
		$(CONTAINER_ENV_ARGS) \
		-v "$(realpath $(SOURCE_DIR)):$(CONTAINER_APP_DIR):Z" \
		"$(IMAGE_NAME)"

debug: $(CONTAINER_FILE) $(IMAGE_BUILT)
	@echo "Running debug shell in $(IMAGE_NAME) with Podman..."
	@podman run --rm -it \
		$(CONTAINER_ENV_ARGS) \
		-v "$(realpath $(SOURCE_DIR)):$(CONTAINER_APP_DIR):Z" \
		"$(IMAGE_NAME)" \
		bash

build: $(IMAGE_BUILT)

$(IMAGE_BUILT): $(CONTAINER_FILE)
	@echo "Building image: $(IMAGE_NAME) with Podman"
	@podman build -t "$(IMAGE_NAME)" "$(CONTEXT_DIR)"
	@echo $(IMAGE_NAME) > $(IMAGE_BUILT)

clean:
	@touch $(IMAGE_BUILT)
	@while IFS= read -r image; do \
		echo "Removing containers using image: $$image"; \
		podman ps -aq --filter ancestor=$$image | xargs -r podman rm -f; \
		echo "Removing image: $$image"; \
		podman rmi -f $$image || true; \
	done < $(IMAGE_BUILT);
	@rm -f $(IMAGE_BUILT)

	@echo "Removing python app cache"
	@podman run --rm \
		-v "$(realpath $(SOURCE_DIR)):$(CONTAINER_APP_DIR):Z" \
		alpine \
		find $(CONTAINER_APP_DIR) -type d -name "__pycache__" -exec rm -rf {} +


.PHONY: run debug build clean
