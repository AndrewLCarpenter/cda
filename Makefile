# Make targets for CDA


mongo:
	docker-compose up -d

test:
	pytest exchanges/ --cov=exchanges

requirements:
	pip freeze | grep -v "pkg-resources" > requirements.txt

