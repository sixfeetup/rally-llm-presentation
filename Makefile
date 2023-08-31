.PHONY: help clean clean-reveal start watch

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

persist:
	@mkdir persist

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
	-rm -rf data
	-rm -rf persist

setup: check .langchain_venv .llm_venv persist ## Setup the development environment.  You should only have to run this once.
	@echo "$(GREEN)Setting up development environment...$(END)"
	@echo
	@cp -r canned_index/* persist
	@echo
	@echo "Now you need your OpenAI API key.  Go to https://beta.openai.com/account/api-keys and create a new key."
	@.llm_venv/bin/llm keys set openai
	@#.llm_venv/bin/llm logs off
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
	@.llm_venv/bin/llm keys path
	@.llm_venv/bin/python as_code.py

data:
	@echo "$(GREEN)Setting up rally data...$(END)"
	- mkdir data || true
	- (cd data && wget --mirror \
                -I /speakers-2023/,/all/,/speakers/,/sponsors/,/partners/,/agenda/ \
                --no-parent \
                --follow-tags=a \
                --reject '*.js,*.css,*.ico,*.txt,*.gif,*.jpg,*.jpeg,*.png,*.mp3,*.pdf,*.tgz,*.flv,*.avi,*.mpeg,*.iso' \
                --ignore-tags=img,link,script \
                --header="Accept: text/html" \
        https://rallyinnovation.com/ ) || true

extract: data  ## crawl the site and extract the data
	@echo "$(GREEN)Extracting...$(END)"
	@lynx --help >/dev/null 2>&1 || brew install lynx || echo "You need to install lynx to extract the data."
	-echo find data -name "*.html" -exec sh -c 'lynx -dump -nolist "$$0" > "$${0%.html}.txt"' {} \;
	-find data -name "*.html" -exec sh -c 'lynx -dump -nolist "$$0" > "$${0%.html}.txt"' {} \;
	-find data/rallyinnovation.com/all -name "*.html" -exec sh -c './extract_all.py "$$0" > "$${0%.html}.txt"' {} \;
	-find data/rallyinnovation.com/speakers-2023 -name "*.html" -exec sh -c './extract_speaker.py "$$0" > "$${0%.html}.txt"' {} \;

	@echo "$(GREEN)... Done.$(END)"



langchain-example: data persist  ## LLM use as code using langchain with more control over the process.
	.langchain_venv/bin/python langchain_example.py

## Advanced
contact:  ## Contact us to make more than toys.
	@echo "We can be reached at $(BLUE)https://sixfeetup.com$(END)."

## Documentation
help:  ## Render the readme and getting started guide.
	@mdn README.md || cat README.md

slide-theme := minions_dark

index.html: slides.md js/reveal.js dist/theme/$(slide-theme).css ## build presentation and theme
	pandoc -t revealjs -s -V revealjs-url=. \
		-V theme=$(slide-theme) \
		-V width=1200 \
		-V center=false \
		-V autoPlayMedia=false \
		-V hash=true \
		-o "$@" "$<"

js/reveal.js:
	curl -LO https://github.com/hakimel/reveal.js/archive/master.zip
	bsdtar --strip-components=1 --exclude .gitignore --exclude LICENSE --exclude README.md --exclude demo.html --exclude index.html -xf master.zip
	rm master.zip
	npm install

css/theme/source/$(slide-theme).scss: themes/$(slide-theme).scss
	cp "$<" "$@"

dist/theme/$(slide-theme).css: css/theme/source/$(slide-theme).scss
	npm run build -- css-themes

start: index.html ## bulid presentation and start server
	@echo "Starting the local presentation server 🚀"
	@npm start

clean-reveal: ## clean up the working directory
	rm CONTRIBUTING.md || true
	rm LICENSE || true
	rm .npmignore || true
	rm -rf css/ || true
	rm gulpfile.js || true
	rm index.html || true
	rm -rf examples/ || true
	rm -rf js/ || true
	rm -rf lib/ || true
	rm package-lock.json || true
	rm package.json || true
	rm -rf plugin/ || true
	rm -rf test/ || true
	rm -rf node_modules/ || true
	rm -rf dist/ || true

watch: ## Watch for changes and rebuild
	@echo "♻️ Watching for changes..."
	@watchmedo tricks-from tricks.yaml

usage: ## This help.
	@awk 'BEGIN     { FS = ":.*##"; target="";printf "\nUsage:\n  make $(BLUE)<target>\033[33m\n\nTargets:$(END)" } \
		/^[.a-zA-Z_-]+:.*?##/ { if(target=="")print ""; target=$$1; printf " $(BLUE)%-10s$(END) %s\n\n", $$1, $$2 } \
		/^([.a-zA-Z_-]+):/ {if(target=="")print "";match($$0, "(.*):"); target=substr($$0,RSTART,RLENGTH) } \
		/^\t## (.*)/ { match($$0, "[^\t#:\\\\]+"); txt=substr($$0,RSTART,RLENGTH);printf " $(BLUE)%-10s$(END)", target; printf " %s\n", txt ; target=""} \
		/^## (.*)/ {match($$0, "[^\t#\\\\]+"); txt=substr($$0,RSTART,RLENGTH);printf "\n$(YELLOW)%s$(END)\n", txt ; target=""} \
	' $(MAKEFILE_LIST)
	@# https://gist.github.com/gfranxman/73b5dc6369dc684db6848198290330c7#file-makefile

.DEFAULT_GOAL := usage
