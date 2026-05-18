.PHONY: install frontend backend check-backend submit

# Project root (where this Makefile lives)
ROOT := $(CURDIR)
VENV := $(ROOT)/backend/.venv
VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# --- Edit DEFAULT_* before submission (see README). Command-line overrides still work, e.g.:
#     make submit STUDENT_NAME="Ada Lovelace" STUDENT_EMAIL="ada@example.edu"
DEFAULT_STUDENT_NAME := Ahmed Bahbouh
DEFAULT_STUDENT_EMAIL := axb6361@mavs.uta.edu
STUDENT_NAME ?= $(DEFAULT_STUDENT_NAME)
STUDENT_EMAIL ?= $(DEFAULT_STUDENT_EMAIL)

install:
	@bash -c 'set -a && [ -f "$(ROOT)/.env" ] && . "$(ROOT)/.env"; set +a; \
		test -d "$(VENV)" || python3 -m venv "$(VENV)"; \
		"$(VENV_PIP)" install -r "$(ROOT)/backend/requirements.txt" && \
		cd "$(ROOT)" && npm install'

frontend:
	cd "$(ROOT)" && npm start

backend:
	@test -x "$(VENV_PY)" || (echo "Run make install first (creates backend/.venv for PEP 668–safe installs)." && false)
	cd "$(ROOT)/backend" && "$(VENV_PY)" chat.py

# With the server running: GET /chat/hello and /chat/query?q="What is HCI?" (stdlib only; no venv required)
check-backend:
	python3 "$(ROOT)/backend/scripts/check_backend.py"

# Creates a zip of exactly what Git tracks (node_modules, .env, etc. are not tracked).
submit:
ifeq ($(strip $(STUDENT_NAME)),)
	$(error STUDENT_NAME is empty — set it in this Makefile or pass STUDENT_NAME="...")
endif
ifeq ($(strip $(STUDENT_EMAIL)),)
	$(error STUDENT_EMAIL is empty — set it in this Makefile or pass STUDENT_EMAIL="...")
endif
ifeq ("$(strip $(STUDENT_NAME))","Your Name Here")
	$(error Edit DEFAULT_STUDENT_NAME in this Makefile (or pass STUDENT_NAME="...") — still set to the placeholder)
endif
ifeq ("$(strip $(STUDENT_EMAIL))","your.email@example.edu")
	$(error Edit DEFAULT_STUDENT_EMAIL in this Makefile (or pass STUDENT_EMAIL="...") — still set to the placeholder)
endif
	@SAFE_NAME=$$(echo "$(STUDENT_NAME)" | sed 's/[^a-zA-Z0-9._-]/_/g'); \
	SAFE_EMAIL=$$(echo "$(STUDENT_EMAIL)" | sed 's/@/_at_/g' | sed 's/[^a-zA-Z0-9._-]/_/g'); \
	OUT="$(ROOT)/pokechat-submit-$${SAFE_NAME}-$${SAFE_EMAIL}.zip"; \
	git -C "$(ROOT)" archive --format=zip -o "$$OUT" HEAD && \
	echo "Created $$OUT"
