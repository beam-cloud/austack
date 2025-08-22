react-conversation-example:
	python scripts/setup-env.py DEEPGRAM_API_KEY OPENAI_API_KEY
	docker-compose -f examples/conversational/docker/docker-compose.yml up --build

deploy-server:
	bash scripts/deploy-server-beam.sh