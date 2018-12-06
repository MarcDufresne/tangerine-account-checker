build:
	docker build -t tangerine:latest .

run:
	docker run \
		-v $(shell pwd)/config.json:/app/config.json \
		-v $(shell pwd)/client_secret.json:/app/client_secret.json \
		-v $(shell pwd)/credentials.json:/app/credentials.json \
		tangerine:latest
