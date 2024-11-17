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
	BUILD_OUTPUT = Builds/Sim.app/Contents/MacOS/Simulation
	UNITY_ARCHIVE = $(LOCAL_UNITY_DIR)/Unity.pkg
else
	ARCH = $(shell if [ "$$(uname -m)" = "aarch64" ]; then echo "arm64"; else echo "x86_64"; fi)
	UNITY_URL = https://download.unity3d.com/download_unity/$(UNITY_HASH)/LinuxEditorInstaller/Unity-$(UNITY_VERSION).tar.xz
	UNITY_EDITOR = $(LOCAL_UNITY_DIR)/Editor/Unity
	BUILD_OUTPUT = Builds/Sim.x86_64
	UNITY_ARCHIVE = $(LOCAL_UNITY_DIR)/Unity.tar.xz
endif

.PHONY: all clean install-unity build wrap

all: build

$(UNITY_ARCHIVE):
	@echo "Downloading Unity $(UNITY_VERSION)..."
	@mkdir -p $(LOCAL_UNITY_DIR)
	@curl -L $(UNITY_URL) -o $@

$(UNITY_EDITOR): $(UNITY_ARCHIVE)
	@echo "Installing Unity $(UNITY_VERSION)..."
	@if [ "$(shell uname)" = "Darwin" ]; then \
		pkgutil --expand $(UNITY_ARCHIVE) $(LOCAL_UNITY_DIR)/tmp; \
		cd $(LOCAL_UNITY_DIR)/tmp && cat Unity.pkg/Payload | gzip -d | cpio -id; \
		mv $(LOCAL_UNITY_DIR)/tmp/Applications/Unity $(LOCAL_UNITY_DIR)/Unity.app; \
		rm -rf $(LOCAL_UNITY_DIR)/tmp; \
		touch $@; \
	else \
		tar xf $(UNITY_ARCHIVE) -C $(LOCAL_UNITY_DIR); \
		touch $@; \
	fi

build: $(UNITY_EDITOR)
	@echo "Building project..."
	@mkdir -p Builds
	@$(UNITY_EDITOR) \
		-quit -batchmode -nographics \
		-projectPath "$(CURDIR)" \
		-executeMethod Builder.Build \
		-logFile "$(CURDIR)/Builds/build.log"
	@if [ -f "$(BUILD_OUTPUT)" ]; then \
		echo "Build successful!"; \
		$(MAKE) wrap; \
	else \
		echo "Build failed! Check Builds/build.log"; \
		exit 1; \
	fi

wrap:
	@echo "Creating wrapper..."
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo '#!/bin/bash' > Builds/sim; \
		echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> Builds/sim; \
		echo 'export DYLD_FRAMEWORK_PATH="$$SCRIPT_DIR/Sim.app/Contents/Frameworks:$$DYLD_FRAMEWORK_PATH"' >> Builds/sim; \
		echo 'exec "$$SCRIPT_DIR/Sim.app/Contents/MacOS/Simulation" "$$@"' >> Builds/sim; \
	else \
		if command -v autopatchelf >/dev/null 2>&1; then \
			find Builds -type f -executable -exec autopatchelf {} \;; \
		fi; \
		echo '#!/bin/bash' > Builds/sim; \
		echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> Builds/sim; \
		echo 'CURRENT_LD_LIBRARY_PATH="$(LD_LIBRARY_PATH)"' >> Builds/sim; \
		echo 'cd "$$SCRIPT_DIR"' >> Builds/sim; \
		echo 'export LD_LIBRARY_PATH="$$SCRIPT_DIR:$$SCRIPT_DIR/Sim_Data/Plugins/x86_64:$$CURRENT_LD_LIBRARY_PATH"' >> Builds/sim; \
		echo 'exec "./Sim.x86_64" "$$@"' >> Builds/sim; \
	fi
	@chmod +x Builds/sim

clean:
	rm -rf Builds/ $(LOCAL_UNITY_DIR)