OUTPUT_DIR = outputs

# Pip options
PIP_DEPS_PKG_DIR = package
PIP_PLATFORM = manylinux2014_aarch64
PIP_PYTHON_VERSION = 3.10
REQUIREMENT_FILE = requirements.txt

# this is needed to fix that weird Pydantic 'email-validator is None' issue
# see: https://github.com/pydantic/pydantic/discussions/9588
# and https://docs.pydantic.dev/latest/integrations/aws_lambda/#installing-pydantic-for-aws-lambda-functions
UPGRADE_OPTS = pydantic
PIP_OPTS =  --requirement $(REQUIREMENT_FILE) \
			--target ./$(PIP_DEPS_PKG_DIR) \
			--platform $(PIP_PLATFORM) \
			--implementation cp \
			--python-version $(PIP_PYTHON_VERSION) \
			--only-binary=:all: \
			--upgrade $(UPGRADE_OPTS)

ZIP_COMMON_OPTS = -x "*.DS_Store" -x "**/__pycache__/*" -x "__pycache__/"

# .zip to be uploaded
DEPLOYMENT_PACKAGE = deployment_package.zip

.PHONY: build
build:
	@echo "Installing deps\n"
	pip install $(PIP_OPTS)
	@echo "\n"

	@echo "creating output directory\n"
	mkdir -p $(OUTPUT_DIR)
	@echo "\n"

	@echo "Creating .zip\n"
	cd ./package && zip -r ../$(OUTPUT_DIR)/$(DEPLOYMENT_PACKAGE) . $(ZIP_COMMON_OPTS)
	@echo "\n"

	@echo "Appending lambdas to .zip\n"
	zip -r $(OUTPUT_DIR)/$(DEPLOYMENT_PACKAGE) lambdas/** $(ZIP_COMMON_OPTS)
	@echo "\n"

.PHONY: deploy
deploy: $(OUTPUT_DIR)/$(DEPLOYMENT_PACKAGE)
	cd cdk && cdk deploy

diff:
	cd cdk && cdk diff

synth:
	cd cdk && cdk synth