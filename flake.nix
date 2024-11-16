{
  description = "Unity project development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system: 
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        
        # Unity version info
        unityVersion = "2023.2.20";
        changeset = "f1";
        
        # Platform-specific settings
        platformSettings = if pkgs.stdenv.isDarwin then {
          module = "--module mac-il2cpp";
          hubCmd = "/Applications/Unity\\ Hub.app/Contents/MacOS/Unity\\ Hub";
          libs = with pkgs; [
            darwin.apple_sdk.frameworks.CoreServices
            darwin.cctools
          ];
          setupScript = '''';  # No special setup needed for macOS
        } else {
          module = "--module linux-il2cpp";
          hubCmd = "${pkgs.unityhub}/bin/unityhub";
          libs = with pkgs; [
            # X11 and display
            xorg.libX11
            xorg.libXcursor
            xorg.libXrandr
            xorg.libXi
            
            # UI toolkit
            gtk3
            gdk-pixbuf
            cairo
            pango
            libGL
            
            # System
            glib
            icu
            systemd
            unityhub
          ];
          setupScript = ''
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath platformSettings.libs}:$LD_LIBRARY_PATH
            export AUTO_PATCHELF_LIBS=${pkgs.lib.makeLibraryPath platformSettings.libs}
          '';
        };

        # Architecture detection
        arch = if system == "x86_64-linux" then "x86_64"
          else if system == "aarch64-linux" then "arm64"
          else if system == "x86_64-darwin" then "x64"
          else if system == "aarch64-darwin" then "arm64"
          else throw "Unsupported system: ${system}";

        # Create wrapper command
        wrapUnityBinary = pkgs.writeScriptBin "wrap-unity-binary" ''
          #!${pkgs.bash}/bin/bash
          BINARY_PATH="$1"
          OUTPUT_PATH="$2"
          
          if [[ -z "$BINARY_PATH" || -z "$OUTPUT_PATH" ]]; then
            echo "Usage: wrap-unity-binary <binary-path> <output-path>"
            exit 1
          fi
          
          mkdir -p "$(dirname "$OUTPUT_PATH")"
          
          ${if pkgs.stdenv.isDarwin then ''
            cat > "$OUTPUT_PATH" << 'EOF'
            #!/bin/bash
            exec "$BINARY_PATH" "$@"
            EOF
          '' else ''
            # Patch the binary
            echo "Patching binary with autopatchelf..."
            chmod +x "$BINARY_PATH"
            
            # Use common environment setup
            ${platformSettings.setupScript}
            
            # Use autopatchelf
            ${pkgs.autoPatchelfHook}/bin/autopatchelf "$BINARY_PATH"
            
            # Create the wrapper with the same environment
            cat > "$OUTPUT_PATH" << EOF
            #!${pkgs.bash}/bin/bash
            ${platformSettings.setupScript}
            exec "$BINARY_PATH" "\$@"
            EOF
          ''}
          
          chmod +x "$OUTPUT_PATH"
          echo "Created wrapper at $OUTPUT_PATH"
        '';
        protobuf_override = final: prev: { 
          protobuf = prev.protobuf.overridePythonAttrs (oldAttrs: rec {
            version = "3.19.6";
            src = pkgs.fetchPypi {
              pname = "protobuf";
              inherit version;
              sha256 = "sha256-X1VA1XpDBCOJ6HZhxuqlD0fBnGF26M8cTyh67v7MtcQ=";
            };
          });
        };
        python = pkgs.python311.override { packageOverrides = protobuf_override; };
      in
      with pkgs;    
      {
        devShell = mkShell {
          UNITY_VERSION = "${unityVersion}${changeset}";
          buildInputs = [
            (import ./python.nix { python = python; })
            autoPatchelfHook
            patchelf
            wrapUnityBinary
            zlib
          ] ++ platformSettings.libs;

          shellHook = ''
            # Set up Unity Hub command
            unityhub() {
              ${platformSettings.hubCmd} "$@"
            }
            export -f unityhub
            
            echo "Unity development environment ready"
            echo "Architecture: ${arch}"
            
            ${if !stdenv.isDarwin then ''
              # Use common environment setup
              ${platformSettings.setupScript}
              
              echo "Installing Unity ${unityVersion} with platform support if not present..."
              unityhub -- --headless install --version ${unityVersion} --changeset ${changeset} --architecture ${arch} ${platformSettings.module}
            '' else ''
              echo "Install the right version of Unity manually, the one I assume you use is ${unityVersion}"
            ''}
          '';
        };
      }
    );
}
