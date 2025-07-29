.DEFAULT_GOAL := help
SHELL := bash

# In order to better support the new M1 Macs,
# we allow the user to specify an environment variable
# named 'DOCKER_PLATFORM' to indicate what platform
# they would like to build use.
# Example:
#    export set DOCKER_PLATFORM=linux/arm64
docker_platform_option :=
ifneq '$(DOCKER_PLATFORM)' ''
docker_platform_option := --platform $(DOCKER_PLATFORM)
endif

min_coverage_pct := 0
args = $(foreach a,$($(subst -,_,$1)_args),$(if $(value $a),$a='$($a)'))
check_code_quality_args = files disable_noqa
release_args = version
test_args = type match capture min_coverage_pct
pylint_args = display_report disable
tag_version_args = release_candidate_flag
publish_args = branch_name artifactory_user artifactory_password

# set variable project_root to be the current working directory
project_root := $(shell pwd)

# if there is an environment variable named SCM_REPO_NAME - that
# will override the variable project_root
ifneq '$(SCM_REPO_NAME)' ''
project_root := $(SCM_REPO_NAME)
endif

export PROJECT_ROOT := ${project_root}

# Convert hyphens to underscores
export PROJECT_ROOT_UNDERSCORE := $(shell echo $(PROJECT_ROOT) | tr '-' '_')
export PROJECT_ROOT_HYPHEN := $(shell echo $(PROJECT_ROOT) | tr '_' '-')


export PROJECT_SLUG := $(shell basename $(PROJECT_ROOT))
export PROJECT_SLUG_UNDERSCORE := $(shell basename $(PROJECT_ROOT_UNDERSCORE))
export PROJECT_SLUG_HYPHEN := $(shell basename $(PROJECT_ROOT_HYPHEN))

export DO_INTEGRATION_TESTS := FALSE  ## set this to FALSE to skip all integration tests - when true you MUST set any expected environment variables

docker_image_name = $(PROJECT_SLUG_HYPHEN):final
ifneq '$(IMAGE_NAME)' ''
docker_image_name := $(IMAGE_NAME)
endif

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sorted(sys.stdin):
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		if target not in ('verify-not-released'):
			print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

define docker_run_make
	docker run $(docker_platform_option) --rm --user 0:0 -v "$(HOME)/.ssh":/home/user/.ssh:ro -v "$(HOME)/.gitconfig":/home/user/.gitconfig:ro -v "$(HOME)/.jupiterone":/root/.jupiterone:ro -v "$(HOME)/.ssh":/root/.ssh:ro -v "$(HOME)/.gitconfig":/root/.gitconfig:ro -v "$(PWD)":/project -e CI_PROJECT_NAME='$(PROJECT_SLUG_UNDERSCORE)' -e SCM_REPO_NAME='$(PROJECT_SLUG_UNDERSCORE)' -w /project $(PROJECT_SLUG_HYPHEN):test make -f .wpg/DockerMakefile $(1) $(2)
endef

define docker_run
	docker run $(docker_platform_option) -it --rm -v "$(HOME)/.jupiterone":/home/user/.jupiterone:ro -v "$(HOME)/.ssh":/home/user/.ssh:ro -v "$(HOME)/.gitconfig":/home/user/.gitconfig:ro -v "$(HOME)/.jupiterone":/root/.jupiterone:ro -v "$(HOME)/.ssh":/root/.ssh:ro -v "$(HOME)/.gitconfig":/root/.gitconfig:ro -v "$(PWD)":/project  -e CI_PROJECT_NAME='$(PROJECT_SLUG_UNDERSCORE)' -e SCM_REPO_NAME='$(PROJECT_SLUG_UNDERSCORE)' -w /project -p 8000:8000 $(PROJECT_SLUG_HYPHEN):dev-latest bash
endef

define docker_run_final
	docker run $(docker_platform_option) -it --rm -v "$(HOME)/.jupiterone":/home/user/.jupiterone:ro -v "$(HOME)/.ssh":/home/user/.ssh:ro -v "$(HOME)/.gitconfig":/home/user/.gitconfig:ro -v "$(PWD)":/project  --mount type=volume,src="$(PROJECT_SLUG_UNDERSCORE)-venv",dst="/venv" -e CI_PROJECT_NAME='$(PROJECT_SLUG_UNDERSCORE)' -e SCM_REPO_NAME='$(PROJECT_SLUG_UNDERSCORE)' -w /project --mount type=bind,src="$(PWD)/.dockerignore",dst="/project/.dockerignore" --mount type=bind,src="$(PWD)/.gitignore",dst="/project/.gitignore" --mount type=bind,src="$(PWD)/.git",dst="/project/.git"  -p 8000:8000 $(PROJECT_SLUG_HYPHEN):final bash
endef

define docker_run_test
	docker run $(docker_platform_option) -it --rm --user 0:0 -v "$(HOME)/.ssh":/home/user/.ssh:ro -v "$(HOME)/.gitconfig":/home/user/.gitconfig:ro -v "$(PWD)":/project  --mount type=volume,src="$(PROJECT_SLUG_UNDERSCORE)-venv",dst="/venv" -e CI_PROJECT_NAME='$(PROJECT_SLUG_UNDERSCORE)' -e SCM_REPO_NAME='$(PROJECT_SLUG_UNDERSCORE)' -w /project --mount type=bind,src="$(PWD)/.dockerignore",dst="/project/.dockerignore" --mount type=bind,src="$(PWD)/.gitignore",dst="/project/.gitignore" --mount type=bind,src="$(PWD)/.git",dst="/project/.git"  -p 8000:8000 $(PROJECT_SLUG_HYPHEN):test bash
endef

define docker_run_make_tag_version
	docker run $(docker_platform_option) --rm -e DM_GITBOT_SSH_PRIVATE_KEY="$(DM_GITBOT_SSH_PRIVATE_KEY)" -e ARTIFACTORY_USER=$(ARTIFACTORY_USER) -e ARTIFACTORY_PASS=$(ARTIFACTORY_PASS) -v "$(HOME)/.ssh":/home/user/.ssh -v "$(HOME)/.gitconfig":/home/user/.gitconfig -v "$(PWD)":/project -e CI_PROJECT_NAME='$(PROJECT_SLUG_UNDERSCORE)' -e SCM_REPO_NAME='$(PROJECT_SLUG_UNDERSCORE)' -w /project   $(PROJECT_SLUG_HYPHEN):test make -f .wpg/DockerMakefile tag-version release_candidate_flag=$(RC)
endef

define docker_run_notebook
	docker run $(docker_platform_option) -it --rm -v "$(HOME)/.ssh":/home/user/.ssh:ro -v "$(HOME)/.gitconfig":/home/user/.gitconfig:ro -v "$(HOME)/.ssh":/root/.ssh:ro -v "$(HOME)/.gitconfig":/root/.gitconfig:ro -v "$(PWD)":/project  -e CI_PROJECT_NAME='$(PROJECT_SLUG_UNDERSCORE)' -e SCM_REPO_NAME='$(PROJECT_SLUG_UNDERSCORE)' -w /project -p 8888:8888 -p 80:80 $(PROJECT_SLUG_HYPHEN):dev-latest jupyter notebook --allow-root --ip='0.0.0.0' --no-browser --NotebookApp.token='' --notebook-dir=/project/notebooks
endef

define display_virtualenv_warning
	@echo " "
	@echo " "
	@echo "********************************************************************"
	@echo " "
	@echo "    You have a Virtual Environment Activated . . ."
	@echo " "
	@echo "    Please Deactivate the virtual environment "
	@echo "    and try again. "
	@echo " "
	@echo "********************************************************************"
	@echo " "
	@echo " "
endef

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)



# .wpg/.download-poetry: ## Download and Install Poetry if needed
# ifneq '$(VIRTUAL_ENV)' ''
# 	$(call display_virtualenv_warning);
# 	@exit 1;
# endif
# 	python3 -m pip install poetry==1.4.0
# 	poetry config virtualenvs.in-project true
# 	touch .wpg/.just-downloaded
# 	touch $@

.wpg/.download-poetry: ## Download and Install Poetry if needed
ifneq '$(VIRTUAL_ENV)' ''
	$(call display_virtualenv_warning);
	@exit 1;
endif
	poetry config virtualenvs.in-project true
	touch .wpg/.just-downloaded
	touch $@

.wpg/.project_setup: .wpg/.download-poetry ## Initialize project and install dependencies
#.wpg/.project_setup:
	@echo " "
	@echo " "
	@echo "********************************************************************"
	@echo "   One time project setup.  This will take 5 to 10 minutes . . ."
	@echo "   This is a good time to go get a cup of coffee!!"
	@echo "********************************************************************"
	@echo " "
	@echo " "
	git init ## This is safe even if you've already initialized . . .
	poetry config virtualenvs.in-project true
	poetry config --list
	rm -rf .venv
	poetry install -n
ifneq ($(NO_PRE_COMMIT), 1)
	poetry run pre-commit install
endif
	touch $@


.wpg/.local-venv: .wpg/.project_setup ## Create local venv
	@echo "Local Virtual Environment created"
	touch $@

.wpg/.local-docker-image: Dockerfile ## empty target for local docker image
	DOCKER_BUILDKIT=1 docker build $(docker_platform_option) --target develop --build-arg REPO_NAME=$(PROJECT_SLUG_UNDERSCORE) -t $(PROJECT_SLUG_HYPHEN):dev-latest .
	touch $@

.wpg/.test-docker-image: Dockerfile  ## empty target for test docker image
	DOCKER_BUILDKIT=1 docker build $(docker_platform_option) --target test --build-arg REPO_NAME=$(PROJECT_SLUG_UNDERSCORE) -t $(PROJECT_SLUG_HYPHEN):test .
	touch $@

.wpg/.final-docker-image: Dockerfile ## empty target for final docker image
	DOCKER_BUILDKIT=1 docker build $(docker_platform_option) --target final -t $(PROJECT_SLUG_HYPHEN):final .
	touch $@

.clean-local-venv: ## remove local virtual environment
	@(rm -rf .venv)
	@(rm -f .wpg/.download-poetry)
	@(rm -f .wpg/.just-downloaded)
	@(rm -f .wpg/.local-venv)

.clean-local-docker-image: ## remove any existing docker image
	@rm -f .wpg/.local-docker-image

.clean-test-docker-image: ## remove any existing docker image
	@rm -f .wpg/.test-docker-image

.clean-final-docker-image: ## remove any existing docker image
	@rm -f .wpg/.final-docker-image

bump-patch: .wpg/.test-docker-image ## bump version - patch
	$(call docker_run_make, bump-patch)

bump-minor: .wpg/.test-docker-image ## bump version - minor
	$(call docker_run_make, bump-minor)

bump-major: .wpg/.test-docker-image ## bump version - major
	$(call docker_run_make, bump-major)

check: .wpg/.test-docker-image ## run lint, bandit, and other safety checks
	$(call docker_run_make, check)

clean: clean-build clean-pyc clean-test clean-logs ## remove all build, test, coverage and Python artifacts
	@echo "Basic Clean Complete!"

clean-build: ## remove build artifacts
	@rm -fr build/
	@rm -fr dist/
	@rm -fr .eggs/
	@find . -name '*.egg-info' -exec rm -fr {} +
	@find . -name '*.egg' -exec rm -fr {} +

clean-logs: ## remove log files
	@find . -name '*.log' -exec rm -f {} +
	@find . -name 'access_log.txt' -exec rm -f {} +
	@find . -name 'splunk' -exec rm -rf {} +
	@find . -name 'counter_*.db' -exec rm -rf {} +
	@find . -name 'histogram_*.db' -exec rm -rf {} +

clean-pyc: ## remove Python file artifacts
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	@rm -fr .tox/
	@rm -f .coverage
	@rm -fr htmlcov/
	@rm -rf coverage_html/
	@rm -fr .pytest_cache

documentation: .wpg/.local-docker-image ## generate documentation
	$(call docker_run_make, documentation $(call args,$@))

view-documentation: .wpg/.local-venv ## generate documentation and open in a browser
	@(rm -f docs/seceng_jupiterone_client*.rst)
	poetry run sphinx-apidoc -e -M -q -f -o docs $(PROJECT_SLUG_UNDERSCORE) $(PROJECT_SLUG_UNDERSCORE)/cli
	poetry run sphinx-build -b html docs build/html
	open build/html/index.html

dist: .wpg/.test-docker-image ## bundle the project for deployment
	$(call docker_run_make, bundle)

format: .wpg/.test-docker-image ## format source code using Black and iSort
	$(call docker_run_make, format $(call args,$@))

local-docker-image: .wpg/.local-docker-image ## Create a new Local Development Docker Image
	@echo "Local Docker Image is ready."

test-docker-image: .wpg/.test-docker-image ## Create a new Test Docker Image
	@echo "Test Docker Image is ready."

local-venv: .wpg/.local-venv ## create a .venv virtual environment

final-docker-image: .wpg/.final-docker-image ## Create a new Final Docker Image
	@echo "Final Docker Image is ready."

remove-development-volume: ## Remove the named Docker Volume used for development
	@(docker volume rm "$(PROJECT_SLUG_UNDERSCORE)-venv" >/dev/null 2>&1;) || true
	@(rm -rf .venv)
	@(rm -f .wpg/.download-poetry)
	@(rm -f .wpg/.just-downloaded)

test: .wpg/.test-docker-image ## run unit tests
	$(call docker_run_make, test, $(call args,$@))

verify-not-released: .wpg/.test-docker-image ## verify that the current version is not yet released
	$(call docker_run_make, verify-not-released)

work: .wpg/.local-docker-image ## Run the Docker Image and Open a shell script into the docker image
	$(call docker_run)

work-test: .wpg/.test-docker-image ## Start a bash shell in the test Docker Image
	$(call docker_run_test)

work-final: .wpg/.final-docker-image ## Start a bash shell in the final Docker Image
	$(call docker_run_final)

clean-all-but-lock: clean .clean-local-docker-image .clean-test-docker-image .clean-final-docker-image .clean-local-venv remove-development-volume ## clean EVERYTHING, but keep poetry lock file.
	@echo "Clean All But Lockfile Complete!"

clean-deep: clean-all-but-lock ## clean EVERYTHING!
	rm -f poetry.lock
	@(docker images -a | grep "$(PROJECT_SLUG_HYPHEN)" | awk '{print $3}' | uniq | xargs docker rmi --force  >/dev/null 2>&1;) || true
	@echo "Deep Clean Complete!"

clean-deep-rebuild: clean-deep local-venv .wpg/.test-docker-image ## clean EVERYTHING and rebuild virtual environment and test docker image
	@echo "All Clean and Local Docker Image is ready."

rebuild-docker: clean .clean-local-docker-image .clean-test-docker-image .clean-final-docker-image .wpg/test-docker-image ## clean EVERYTHING and rebuild test docker image
	@echo "All Clean and Local Docker Images are ready."

rebuild-venv: clean .clean-local-venv remove-development-volume local-venv ## clean EVERYTHING and rebuild local virtual environment
	@echo "All Clean and Local Virtual Environment is ready."

tf-init: ## Perform Terraform Init on the Terraform Directory
	docker-compose -f deploy/docker-compose.yml run --rm terraform init

tf-dev: ## Perform Terraform Switch to Dev Environment
	docker-compose -f deploy/docker-compose.yml run --rm terraform workspace select dev

tf-env: ## Perform Terraform Show the Workspace Name
	docker-compose -f deploy/docker-compose.yml run --rm terraform workspace show

tf-fmt: ## Perform Terraform Fmt on the Terraform Directory
	docker-compose -f deploy/docker-compose.yml run --rm terraform fmt

tf-validate: ## Perform Terraform Validate on the Terraform Directory
	docker-compose -f deploy/docker-compose.yml run --rm terraform validate

tf-plan: ## Perform Terraform Plan on the Terraform Directory
	docker-compose -f deploy/docker-compose.yml run --rm terraform plan

tf-apply: ## Perform Terraform apply on the Terraform Directory
	docker-compose -f deploy/docker-compose.yml run --rm terraform apply

tf-destroy: ## Perform Terraform Destroy on the Terraform Directory
	docker-compose -f deploy/docker-compose.yml run --rm terraform destroy

run-notebook: .wpg/.local-docker-image ## Start up a Jupyter Notebook Server
	@mkdir -p notebooks
	$(call docker_run_notebook)
