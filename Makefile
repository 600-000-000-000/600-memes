.PHONY: build run

IMAGE_NAME = 600-memes
CONTAINER_NAME = 600-memes
PORT = 8000

build:
	docker build -t $(IMAGE_NAME) .

run:
	@echo "Restarting container..."
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker run --restart always -d --name $(CONTAINER_NAME) \
		-p $(PORT):8000 \
		-v $(PWD)/uploads:/app/uploads \
		$(IMAGE_NAME)
	@echo "Container $(CONTAINER_NAME) is running at http://localhost:$(PORT)"
