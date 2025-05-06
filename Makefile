.PHONY: build clean deploy install-deps build-layer

build:
	sam build --use-container

clean:
	rm -rf .aws-sam/
	rm -rf layers/python/*

deploy:
	sam deploy --stack-name lambdas-init \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		--capabilities CAPABILITY_IAM

build-layer:
	mkdir -p layers/python
	python -m pip install -r layers/requirements.txt -t layers/python/

install-deps:
	for dir in src/*/; do \
		if [ -f "$$dir/requirements.txt" ]; then \
			python -m pip install --upgrade pip && \
			python -m pip install wheel setuptools && \
			python -m pip install -r "$$dir/requirements.txt" -t "$$dir/" --no-cache-dir; \
		fi \
	done