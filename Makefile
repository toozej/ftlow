# Set sane defaults for Make
SHELL = bash
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# Set default goal such that `make` runs `make help`
.DEFAULT_GOAL := help

IMAGE_NAME := toozej/ftlow
IMAGE_TAG := latest

.PHONY: all build run help

all: build run ## Run default workflow

build: ## Build Dockerized project
	docker build -f Dockerfile -t $(IMAGE_NAME):$(IMAGE_TAG) .

run: ## Run Dockerized project
	docker run --rm --name ftlow -p 5000:5000 $(IMAGE_NAME):$(IMAGE_TAG)

help: ## Display help text
	@grep -E '^[a-zA-Z_-]+ ?:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
