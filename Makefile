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
	
	@for binary in \
		$(UNITY_EDITOR) \
		$(LOCAL_UNITY_DIR)/Editor/Data/Resources/Licensing/Client/Unity.Licensing.Client \
		$(LOCAL_UNITY_DIR)/Editor/Data/Resources/PackageManager/Server/UnityPackageManager \
		$(LOCAL_UNITY_DIR)/Editor/Data/NetCoreRuntime/dotnet \
		$(LOCAL_UNITY_DIR)/Editor/Data/Tools/Compilation/Unity.ILPP.Trigger/Unity.ILPP.Trigger \
		$(LOCAL_UNITY_DIR)/Editor/Data/Tools/Compilation/Unity.ILPP.Runner/Unity.ILPP.Runner \
		$(LOCAL_UNITY_DIR)/Editor/Data/Tools/UnityAutoQuitter \
		$(LOCAL_UNITY_DIR)/Editor/Data/bee_backend \
		$(LOCAL_UNITY_DIR)/Editor/Data/Tools/BuildPipeline/BeeLocalCacheTool \
		$(LOCAL_UNITY_DIR)/Editor/Data/Tools/netcorerun/netcorerun \
		$(LOCAL_UNITY_DIR)/Editor/Data/Tools/UnityShaderCompiler \
		$(LOCAL_UNITY_DIR)/Editor/Data/il2cpp/build/deploy/UnityLinker \
		$(LOCAL_UNITY_DIR)/Editor/Data/MonoBleedingEdge/bin/mono; do \
		cp $$binary $$binary.tmp && \
		patchelf --set-interpreter "$(shell cat $(NIX_CC)/nix-support/dynamic-linker)" $$binary.tmp && \
		mv $$binary.tmp $$binary; \
	done

	@if $(LOCAL_UNITY_DIR)/Editor/Data/Resources/Licensing/Client/Unity.Licensing.Client --showEntitlements | grep -q 'No licenses were found.'; then \
		echo "No Unity licenses were found, please login to Unity..."; echo; \
		read -p "Username: " username; \
		read -s -p "Password: " password; echo; \
		$(LOCAL_UNITY_DIR)/Editor/Data/Resources/Licensing/Client/Unity.Licensing.Client --username $$username --password $$password --activate-all --include-personal; \
	else \
		echo "Unity license(s) found."; \
	fi

$(BUILD_OUTPUT): $(UNITY_EDITOR)
	@mkdir -p $(dir $(BUILD_OUTPUT))
	@$(UNITY_EDITOR) \
		-quit -batchmode -nographics \
		-projectPath "$(CURDIR)" \
		-executeMethod Builder.Build \
		-logFile "$(CURDIR)/Builds/build.log"; \
	if [ $$? -ne 0 ]; then \
		if grep -q -E "Could not start dynamically linked executable: .*/Library/PackageCache/com.unity.burst@1.8.17/.Runtime/burst-lld-16-hostlin" $(CURDIR)/Builds/build.log; then \
			patchelf --set-interpreter "$(shell cat $(NIX_CC)/nix-support/dynamic-linker)" $(CURDIR)/Library/PackageCache/com.unity.burst@1.8.17/.Runtime/burst-lld-16-hostlin; \
			rm -rf $(BUILD_OUTPUT)/{*,.[!.]*,..?*}; \
			$(UNITY_EDITOR) \
				-quit -batchmode -nographics \
				-projectPath "$(CURDIR)" \
				-executeMethod Builder.Build \
				-logFile "$(CURDIR)/Builds/build.log"; \
		else \
	    	echo "Build failed, check Builds/build.log for more information"; \
		fi; \
	fi

Builds/sim: $(BUILD_OUTPUT)
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo '#!/bin/bash' > $@; \
		echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> $@; \
		echo 'export DYLD_FRAMEWORK_PATH="$$SCRIPT_DIR/Sim.app/Contents/Frameworks:$$DYLD_FRAMEWORK_PATH"' >> $@; \
		echo 'exec "$$SCRIPT_DIR/$(RELATIVE_PATH)" "$$@"' >> $@; \
	else \
		cd Builds && \
		patchelf --set-interpreter "$(shell cat $(NIX_CC)/nix-support/dynamic-linker)" $(RELATIVE_PATH) && \
		patchelf --force-rpath --set-rpath '$$ORIGIN:$(RUNTIME_DEPS)' $(RELATIVE_PATH) && \
		patchelf --force-rpath --set-rpath '$$ORIGIN:$(RUNTIME_DEPS)' UnityPlayer.so && \
		ln -sf $(RELATIVE_PATH) sim; \
	fi
	@chmod +x $@

.PHONY: clean
clean:
	rm -rf Builds/ $(LOCAL_UNITY_DIR)