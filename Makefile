# Unity version info
UNITY_BASE_VERSION ?= 2023.2.20
UNITY_CHANGESET ?= 1
UNITY_HASH = 0e25a174756c
UNITY_VERSION = $(UNITY_BASE_VERSION)f$(UNITY_CHANGESET)

# Local Unity installation directory
LOCAL_UNITY_DIR = .unity
UNITY_DOWNLOAD = $(LOCAL_UNITY_DIR)/Unity-$(UNITY_VERSION)

# OS-specific settings
ifeq ($(shell uname),Darwin)
	ARCH = $(shell if [ "$$(uname -m)" = "arm64" ]; then echo "arm64"; else echo "x64"; fi)
	UNITY_URL = https://download.unity3d.com/download_unity/$(UNITY_HASH)/MacEditorInstaller$(if $(filter arm64,$(ARCH)),Arm64,)/Unity-$(UNITY_VERSION).pkg
	UNITY_EDITOR = $(LOCAL_UNITY_DIR)/Unity.app/Contents/MacOS/Unity
	RELATIVE_PATH = Sim.app/Contents/MacOS/Simulation
else
	ARCH = $(shell if [ "$$(uname -m)" = "aarch64" ]; then echo "arm64"; else echo "x86_64"; fi)
	UNITY_URL = https://download.unity3d.com/download_unity/$(UNITY_HASH)/LinuxEditorInstaller/Unity-$(UNITY_VERSION).tar.xz
	UNITY_EDITOR = $(LOCAL_UNITY_DIR)/Editor/Unity
	RELATIVE_PATH = Sim.x86_64
endif

BUILD_OUTPUT = Builds/$(RELATIVE_PATH)

.PHONY: build
build: Builds/sim

$(UNITY_EDITOR):
	@echo "Installing Unity..."
	@mkdir -p $(LOCAL_UNITY_DIR)
	@if [ "$(shell uname)" = "Darwin" ]; then \
		curl -L $(UNITY_URL) -o $(LOCAL_UNITY_DIR)/Unity.pkg && \
		pkgutil --expand-full $(LOCAL_UNITY_DIR)/Unity.pkg $(LOCAL_UNITY_DIR)/tmp && \
		mv $(LOCAL_UNITY_DIR)/tmp/Unity/Unity.app $(LOCAL_UNITY_DIR)/Unity.app && \
		rm -rf $(LOCAL_UNITY_DIR)/tmp $(LOCAL_UNITY_DIR)/Unity.pkg; \
	else \
		curl -L $(UNITY_URL) -o $(LOCAL_UNITY_DIR)/Unity.tar.xz && \
		tar xf $(LOCAL_UNITY_DIR)/Unity.tar.xz -C $(LOCAL_UNITY_DIR) && \
		rm $(LOCAL_UNITY_DIR)/Unity.tar.xz; \
	fi

$(BUILD_OUTPUT): $(UNITY_EDITOR)
	@mkdir -p $(dir $(BUILD_OUTPUT))
	@$(UNITY_EDITOR) \
		-quit -batchmode -nographics \
		-projectPath "$(CURDIR)" \
		-executeMethod Builder.Build \
		-logFile "$(CURDIR)/Builds/build.log"

Builds/sim: $(BUILD_OUTPUT)
	@cd Builds && \
	if [ "$(shell uname)" = "Linux" ]; then \
		patchelf --set-interpreter "$(shell cat $(NIX_CC)/nix-support/dynamic-linker)" $(RELATIVE_PATH) && \
		patchelf --force-rpath --set-rpath '$$ORIGIN:$(RUNTIME_DEPS)' $(RELATIVE_PATH) && \
		patchelf --force-rpath --set-rpath '$$ORIGIN:$(RUNTIME_DEPS)' UnityPlayer.so; \
	fi && \
	ln -sf $(RELATIVE_PATH) sim

.PHONY: clean
clean:
	rm -rf Builds/ $(LOCAL_UNITY_DIR)