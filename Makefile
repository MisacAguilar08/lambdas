.PHONY: build clean deploy install-deps

build:
	sam build --use-container

clean:
	rm -rf .aws-sam/

deploy:
	sam deploy --stack-name lambdas-init \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		--capabilities CAPABILITY_IAM

install-deps:
	for dir in src/*/; do \
		if [ -f "$dir/requirements.txt" ]; then \
			python -m pip install --upgrade pip && \
			python -m pip install wheel setuptools && \
			python -m pip install -r "$dir/requirements.txt" -t "$dir/" --no-cache-dir; \
		fi \
	done