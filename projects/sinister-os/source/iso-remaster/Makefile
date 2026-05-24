# Makefile -- Sinister OS ISO remaster
# Author: RKOJ-ELENO :: 2026-05-24
#
# One-liner targets for the iso-remaster pipeline. Run from this directory:
#   make build-image   # build the docker container once
#   make remaster      # produce a fresh Sinister OS ISO
#   make verify        # check size + sha256 + xorriso report on the output
#   make clean         # wipe out/ + workspace
#   make help          # show this list

SHELL          := /bin/bash
DOCKER         ?= docker
IMAGE_TAG      ?= sinister-iso-remaster

# Inputs / outputs (relative to this Makefile's directory)
HERE           := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SOURCE_DIR     := $(abspath $(HERE)/..)
INPUT_ISO      ?= $(SOURCE_DIR)/iso-base/cachyos-hyprland.iso
OVERLAY_DIR    ?= $(SOURCE_DIR)/sinister-overlay
OUT_DIR        := $(HERE)/out
LOG_DIR        := $(HERE)/_logs
VERSION_TAG    ?= v1
UTC_STAMP      := $(shell date -u +%Y%m%dT%H%M%SZ)
OUTPUT_ISO     := $(OUT_DIR)/sinister-os-$(UTC_STAMP).iso
LATEST_ISO     := $(shell ls -1t $(OUT_DIR)/sinister-os-*.iso 2>/dev/null | head -1)

.DEFAULT_GOAL := help

.PHONY: help build-image remaster verify clean shell tree-overlay

help:
	@echo "Sinister OS iso-remaster -- available targets:"
	@echo ""
	@echo "  make build-image    Build the docker container (one-time, ~3-5 min)"
	@echo "  make remaster       Remaster the CachyOS ISO with the Sinister overlay"
	@echo "  make verify         Verify size + sha256 + xorriso report of latest output"
	@echo "  make shell          Drop into the remaster container interactively"
	@echo "  make tree-overlay   Show the overlay directory tree (debug)"
	@echo "  make clean          Remove out/ + _logs/"
	@echo ""
	@echo "Variables (override on command line):"
	@echo "  IMAGE_TAG   = $(IMAGE_TAG)"
	@echo "  INPUT_ISO   = $(INPUT_ISO)"
	@echo "  OVERLAY_DIR = $(OVERLAY_DIR)"
	@echo "  OUTPUT_ISO  = $(OUTPUT_ISO)"
	@echo "  VERSION_TAG = $(VERSION_TAG)"

build-image:
	@echo "[make] building docker image $(IMAGE_TAG) from $(HERE)/Dockerfile"
	$(DOCKER) build -t $(IMAGE_TAG) $(HERE)

remaster: | $(OUT_DIR) $(LOG_DIR)
	@echo "[make] remastering $(INPUT_ISO) -> $(OUTPUT_ISO)"
	@if [ ! -f "$(INPUT_ISO)" ]; then \
		echo "ERROR: input ISO not found at $(INPUT_ISO)"; exit 3; \
	fi
	@if [ ! -d "$(OVERLAY_DIR)" ]; then \
		echo "ERROR: overlay dir not found at $(OVERLAY_DIR); sibling agent may not have finished"; \
		exit 2; \
	fi
	$(DOCKER) run --rm --privileged \
		-v "$(SOURCE_DIR)":/sinister-os \
		-v "$(OUT_DIR)":/out \
		-v "$(LOG_DIR)":/logs \
		$(IMAGE_TAG) \
		bash /sinister-os/iso-remaster/remaster.sh \
			-i /sinister-os/iso-base/$(notdir $(INPUT_ISO)) \
			-o /out/$(notdir $(OUTPUT_ISO)) \
			-v $(VERSION_TAG) \
			--overlay /sinister-os/sinister-overlay \
		2>&1 | tee $(LOG_DIR)/remaster-$(UTC_STAMP).log

verify:
	@if [ -z "$(LATEST_ISO)" ]; then echo "ERROR: no ISO in $(OUT_DIR)"; exit 1; fi
	@echo "[make] verifying $(LATEST_ISO)"
	@echo "size:"
	@ls -lh "$(LATEST_ISO)"
	@echo ""
	@echo "sha256:"
	@if [ -f "$(LATEST_ISO).sha256" ]; then cat "$(LATEST_ISO).sha256"; \
	 else sha256sum "$(LATEST_ISO)"; fi
	@echo ""
	@echo "xorriso report:"
	$(DOCKER) run --rm \
		-v "$(OUT_DIR)":/out \
		$(IMAGE_TAG) \
		xorriso -indev /out/$(notdir $(LATEST_ISO)) -report_about ALL 2>&1 | head -80

shell: | $(OUT_DIR) $(LOG_DIR)
	$(DOCKER) run --rm -it --privileged \
		-v "$(SOURCE_DIR)":/sinister-os \
		-v "$(OUT_DIR)":/out \
		-v "$(LOG_DIR)":/logs \
		$(IMAGE_TAG) bash

tree-overlay:
	@if [ -d "$(OVERLAY_DIR)" ]; then \
		find "$(OVERLAY_DIR)" -maxdepth 4 | sort; \
	else \
		echo "(overlay dir not present at $(OVERLAY_DIR))"; \
	fi

clean:
	@echo "[make] cleaning out/ + _logs/"
	rm -rf "$(OUT_DIR)" "$(LOG_DIR)"

$(OUT_DIR):
	mkdir -p "$(OUT_DIR)"

$(LOG_DIR):
	mkdir -p "$(LOG_DIR)"
