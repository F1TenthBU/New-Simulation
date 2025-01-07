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

.PHONY: build patch-unity-editor
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

patch-unity-editor: $(UNITY_EDITOR)
	@if [ "$(shell uname)" != "Darwin" ]; then \
		echo "Patching Unity Editor libraries..." && \
		cd $(LOCAL_UNITY_DIR)/Editor && \
		find . -name "*.so" -type f -exec sh -c '\
			ORIGIN_PATH="$$ORIGIN"; \
			if [[ "{}" == *"/Data/Tools/"* ]]; then \
				ORIGIN_PATH="$$ORIGIN:$$ORIGIN/.."; \
			fi; \
			echo "Patching {} with RPATH $$ORIGIN:$$ORIGIN/../../:$$ORIGIN/Data/Tools:$$ORIGIN/Data/il2cpp/build/deploy:$$ORIGIN/Data/MonoBleedingEdge/x86_64:$(RUNTIME_DEPS)" && \
			patchelf --force-rpath --set-rpath "$$ORIGIN:$$ORIGIN/../../:$$ORIGIN/Data/Tools:$$ORIGIN/Data/il2cpp/build/deploy:$$ORIGIN/Data/MonoBleedingEdge/x86_64:$(RUNTIME_DEPS)" "{}" || echo "Failed to patch {}" \
		' \; && \
		echo "Unity Editor library patching complete."; \
	fi

.PHONY: check-deps
check-deps: $(UNITY_EDITOR)
	@if [ "$(shell uname)" != "Darwin" ]; then \
		echo "Checking Unity Editor dependencies..." && \
		cd $(LOCAL_UNITY_DIR)/Editor && \
		echo "=== Missing dependencies ===" && \
		(ldd Unity 2>/dev/null | grep "not found" || true) && \
		find . -name "*.so" -type f -exec sh -c '\
			MISSING=$$(ldd "{}" 2>/dev/null | grep "not found"); \
			if [ ! -z "$$MISSING" ]; then \
				echo "\n=== Missing dependencies for {}: ==="; \
				echo "$$MISSING"; \
			fi \
		' \; && \
		echo "Dependencies check complete."; \
	fi

$(BUILD_OUTPUT): patch-unity-editor
	@mkdir -p $(dir $(BUILD_OUTPUT))
	@$(UNITY_EDITOR) \
		-quit -batchmode -nographics \
		-projectPath "$(CURDIR)" \
		-executeMethod Builder.Build \
		-logFile "$(CURDIR)/Builds/build.log"

Builds/sim: $(BUILD_OUTPUT)
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo '#!/bin/bash' > $@; \
		echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> $@; \
		echo 'export DYLD_FRAMEWORK_PATH="$$SCRIPT_DIR/Sim.app/Contents/Frameworks:$$DYLD_FRAMEWORK_PATH"' >> $@; \
		echo 'exec "$$SCRIPT_DIR/$(RELATIVE_PATH)" "$$@"' >> $@; \
	else \
		cd Builds && \
		echo "Patching build output..." && \
		patchelf --set-interpreter "$(shell cat $(NIX_CC)/nix-support/dynamic-linker)" $(RELATIVE_PATH) && \
		patchelf --force-rpath --set-rpath '$$ORIGIN:$(RUNTIME_DEPS)' $(RELATIVE_PATH) && \
		find . -name "*.so" -exec patchelf --force-rpath --set-rpath '$$ORIGIN:$(RUNTIME_DEPS)' {} \; && \
		ln -sf $(RELATIVE_PATH) sim && \
		echo "Build output patching complete."; \
	fi
	@chmod +x $@

.PHONY: clean
clean:
	rm -rf Builds/ $(LOCAL_UNITY_DIR)