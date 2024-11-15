#!/usr/bin/env bash

# Function to get the latest Unity editor path
get_unity_path() {
    UNITY_VERSION=$1
    # Get the installation path
    INSTALL_PATH=$(unityhub -- --headless install-path -g)
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "$INSTALL_PATH/$UNITY_VERSION/Unity.app/Contents/MacOS/Unity"
    else
        echo "$INSTALL_PATH/$UNITY_VERSION/Editor/Unity"
    fi
}

# Function to get build output path based on OS
get_build_output() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Builds/Sim.app/Contents/MacOS/Sim"  # Path to actual binary in .app bundle
    else
        echo "Builds/Sim.x86_64"
    fi
}

# Function to patch the built binary
patch_binary() {
    local BUILD_PATH=$1
    if [[ "$OSTYPE" == "linux"* ]]; then
        echo "Patching Linux binary with autopatchelf..."
        
        # Make sure the binary is executable
        chmod +x "$BUILD_PATH"
        
        # Patch the binary and its dependencies
        find "$(dirname "$BUILD_PATH")" -type f -executable -exec patchelf --set-interpreter "$(cat $NIX_CC/nix-support/dynamic-linker)" {} \; 2>/dev/null || true
        
        # Use autoPatchelfHook if available
        if command -v autopatchelf &> /dev/null; then
            autopatchelf "$BUILD_PATH"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Patching macOS binary..."
        
        # Make sure the binary and app bundle are executable
        chmod +x "$BUILD_PATH"
        chmod -R +x "$(dirname "$(dirname "$(dirname "$BUILD_PATH")")")"
        
        # On macOS, we need to update the rpath
        if command -v install_name_tool &> /dev/null; then
            # Add rpath to Frameworks directory
            install_name_tool -add_rpath "@executable_path/../Frameworks" "$BUILD_PATH" 2>/dev/null || true
            # Add rpath to Libraries directory
            install_name_tool -add_rpath "@executable_path/../Libraries" "$BUILD_PATH" 2>/dev/null || true
        fi
    fi
    
    echo "Patching complete"
}

# Function to build Unity project
build_unity_project() {
    local PROJECT_PATH=$1
    local UNITY_VERSION=$2
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

    # Check if build was successful and patch accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -d "$PROJECT_PATH/Builds/Sim.app" ]; then
            echo "Build successful! Output at: $PROJECT_PATH/Builds/Sim.app"
            patch_binary "$PROJECT_PATH/$BUILD_OUTPUT"
        else
            echo "Build failed! Check $PROJECT_PATH/Builds/build.log for details"
            exit 1
        fi
    else
        if [ -f "$PROJECT_PATH/$BUILD_OUTPUT" ]; then
            echo "Build successful! Output at: $PROJECT_PATH/$BUILD_OUTPUT"
            patch_binary "$PROJECT_PATH/$BUILD_OUTPUT"
        else
            echo "Build failed! Check $PROJECT_PATH/Builds/build.log for details"
            exit 1
        fi
    fi
}

# Convert current directory to absolute path and pass it
build_unity_project "$(pwd)" $1