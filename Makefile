.PHONY: help

.EXPORT_ALL_VARIABLES:

LLM_USER_PATH = ./llm-config

# colors
BLUE:=$(shell echo "\033[0;36m")
GREEN:=$(shell echo "\033[0;32m")
YELLOW:=$(shell echo "\033[0;33m")
RED:=$(shell echo "\033[0;31m")
END:=$(shell echo "\033[0m")


## Before you start
check: ## System check
	@python -c "import sys; assert sys.version_info >= (3,9), 'You need at least python 3.9'"
	@echo "$(GREEN)Looks good.$(END)"

.llm_venv:
	@echo "$(GREEN)Setting up llm environment...$(END)"
	python -m venv .llm_venv
	.llm_venv/bin/python -m pip install --upgrade pip
	.llm_venv/bin/pip install -r llm-requirements.txt
	@echo "$(GREEN)... Done.$(END)"
	@echo

.langchain_venv:
	@echo "$(GREEN)Setting up langchain environment...$(END)"
	python -m venv .langchain_venv
	.langchain_venv/bin/python -m pip install --upgrade pip
	.langchain_venv/bin/pip install -r langchain-requirements.txt
	@echo "$(GREEN)... Done.$(END)"
	@echo

clean:
	-rm -rf .langchain_ven
	-rm -rf .llm_venv

setup: check clean .langchain_venv .llm_venv   ## Setup the development environment.  You should only have to run this once.
	@echo "$(GREEN)Setting up development environment...$(END)"
	@echo
	@echo
	@echo "Now you need your OpenAI API key.  Go to https://beta.openai.com/account/api-keys and create a new key."
	@.venv/bin/llm keys set openai
	@#.venv/bin/llm logs off
	@echo "$(GREEN)... Done.$(END)"

## Beginner
ask-openai: ## Ask a question using the naive approach.  ( may throw an ignorable error on macOS )
	@#echo "$(GREEN)Starting the presentation...$(END)"
	@.llm_venv/bin/llm "What's the easiest way to get started with large language models?" 2>/dev/null
	@echo "$(GREEN)... Done.$(END)"


ask-orca-mini: ## Ask a question using the orca-mini-7b model.
	@echo "$(GREEN)Install llm-gpt4all...$(END)"
	@.llm_venv/bin/llm install llm-gpt4all 2>/dev/null
	@echo "$(GREEN)... The ask the model ...$(END)"
	-.llm_venv/bin/llm prompt -m orca-mini-7b "What's the easiest way to get started with large language models?" 2>/dev/null || true
	@echo "$(GREEN)... Done.$(END)"

## Intermediate
as-code:  ## LLM use as code
	llm keys path
	.llm_venv/bin/python as_code.py

as-code-with-more-control:  ## LLM use as code with more control over the process.
	.langchain_venv/bin/python as_code_more_control.py

## Advanced
contact:  ## Contact us to productionize.
	@echo "We can be reached at $(BLUE)https://sixfeetup.com$(END)."

## Documentation
help:  ## Render the readme and getting started guide.
	@mdn README.md || cat README.md


usage: ## This help.
	@awk 'BEGIN     { FS = ":.*##"; target="";printf "\nUsage:\n  make $(BLUE)<target>\033[33m\n\nTargets:$(END)" } \
		/^[.a-zA-Z_-]+:.*?##/ { if(target=="")print ""; target=$$1; printf " $(BLUE)%-10s$(END) %s\n\n", $$1, $$2 } \
		/^([.a-zA-Z_-]+):/ {if(target=="")print "";match($$0, "(.*):"); target=substr($$0,RSTART,RLENGTH) } \
		/^\t## (.*)/ { match($$0, "[^\t#:\\\\]+"); txt=substr($$0,RSTART,RLENGTH);printf " $(BLUE)%-10s$(END)", target; printf " %s\n", txt ; target=""} \
		/^## (.*)/ {match($$0, "[^\t#\\\\]+"); txt=substr($$0,RSTART,RLENGTH);printf "\n$(YELLOW)%s$(END)\n", txt ; target=""} \
	' $(MAKEFILE_LIST)
	@# https://gist.github.com/gfranxman/73b5dc6369dc684db6848198290330c7#file-makefile

.DEFAULT_GOAL := usage
