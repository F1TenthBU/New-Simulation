#!/usr/bin/env bash

# Default Unity version
DEFAULT_VERSION="2023.2.20f1"

# Function to find Unity Hub command
get_unity_hub_cmd() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Check for Unity Hub in standard macOS location
        if [ -f "/Applications/Unity Hub.app/Contents/MacOS/Unity Hub" ]; then
            echo "/Applications/Unity Hub.app/Contents/MacOS/Unity Hub"
            return
        fi
    else
        # Check for Unity Hub in PATH
        if command -v unityhub &> /dev/null; then
            echo "unityhub"
            return
        fi
    fi
    echo "Error: Unity Hub not found"
    exit 1
}

# Function to get the latest Unity editor path
get_unity_path() {
    UNITY_VERSION=$1
    # Get the installation path
    UNITY_HUB=$(get_unity_hub_cmd)
    INSTALL_PATH=$("$UNITY_HUB" -- --headless install-path -g)
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$INSTALL_PATH/$UNITY_VERSION/Unity.app/Contents/MacOS/Unity"
    else
        echo "$INSTALL_PATH/$UNITY_VERSION/Editor/Unity"
    fi
}

# Function to ensure Unity version is installed
ensure_unity_version() {
    local VERSION=$1
    local UNITY_HUB=$(get_unity_hub_cmd)
    
    # Get architecture
    local ARCH
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ $(uname -m) == "arm64" ]]; then
            ARCH="arm64"
        else
            ARCH="x64"
        fi
        MODULE="--module mac-mono"
    else
        if [[ $(uname -m) == "aarch64" ]]; then
            ARCH="arm64"
        else
            ARCH="x86_64"
        fi
        MODULE="--module linux-il2cpp"
    fi
    
    echo "Checking Unity version $VERSION for $ARCH"
    # Split version into version and changeset if provided in format version.changeset
    if [[ $VERSION == *"f"* ]]; then
        local BASE_VERSION=$(echo $VERSION | cut -d'f' -f1)
        local CHANGESET="f$(echo $VERSION | cut -d'f' -f2)"
        "$UNITY_HUB" -- --headless install --version "$BASE_VERSION" --changeset "$CHANGESET" --architecture "$ARCH" $MODULE
    else
        "$UNITY_HUB" -- --headless install --version "$VERSION" --architecture "$ARCH" $MODULE
    fi
}

# Function to get build output path based on OS
get_build_output() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Builds/Sim.app/Contents/MacOS/Simulation"
    else
        echo "Builds/Sim.x86_64"
    fi
}

# Function to build Unity project
build_unity_project() {
    local PROJECT_PATH=$1
    local UNITY_VERSION=$2
    
    # Ensure Unity version is installed
    ensure_unity_version "$UNITY_VERSION"
    
    local BUILD_OUTPUT=$(get_build_output)
    local UNITY_PATH=$(get_unity_path $UNITY_VERSION)
    
    if [[ ! -f "$UNITY_PATH" ]]; then
        echo "Error: Unity editor not found at $UNITY_PATH"
        exit 1
    fi
    
    echo "Using Unity at: $UNITY_PATH"
    echo "Building project at: $PROJECT_PATH"
    echo "Build will be output to: $BUILD_OUTPUT"
    
    # Create Builds directory if it doesn't exist
    mkdir -p "$PROJECT_PATH/Builds"
    
    "$UNITY_PATH" \
        -quit \
        -batchmode \
        -nographics \
        -projectPath "$PROJECT_PATH" \
        -executeMethod Builder.Build \
        -logFile "$PROJECT_PATH/Builds/build.log"

    # Check if build was successful and wrap accordingly
    if [ -f "$PROJECT_PATH/$BUILD_OUTPUT" ]; then
        echo "Build successful! Output at: $PROJECT_PATH/$BUILD_OUTPUT"
        wrap_unity_binary "$PROJECT_PATH/$BUILD_OUTPUT" "$PROJECT_PATH/Builds/sim"
    else
        echo "Build failed! Check $PROJECT_PATH/Builds/build.log for details"
        exit 1
    fi
}

# Function to wrap Unity binary
wrap_unity_binary() {
    local BINARY_PATH="$1"
    local OUTPUT_PATH="$2"
    
    if [[ -z "$BINARY_PATH" || -z "$OUTPUT_PATH" ]]; then
        echo "Usage: wrap_unity_binary <binary-path> <output-path>"
        exit 1
    fi
    
    mkdir -p "$(dirname "$OUTPUT_PATH")"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        cat > "$OUTPUT_PATH" << 'EOF'
#!/bin/bash
exec "$BINARY_PATH" "$@"
EOF
    else
        # Patch the binary if autopatchelf is available
        if command -v autopatchelf &> /dev/null; then
            echo "Patching binary with autopatchelf..."
            chmod +x "$BINARY_PATH"
            autopatchelf "$BINARY_PATH"
        fi
        
        # Create the wrapper with current LD_LIBRARY_PATH
        cat > "$OUTPUT_PATH" << EOF
#!/bin/bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH
exec "$BINARY_PATH" "\$@"
EOF
    fi
    
    chmod +x "$OUTPUT_PATH"
    echo "Created wrapper at $OUTPUT_PATH"
}

# Use provided version or default
VERSION="${1:-$DEFAULT_VERSION}"
build_unity_project "$(pwd)" "$VERSION"