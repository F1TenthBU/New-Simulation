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
        
        unityVersion = "2023.2.20";
        changeset = "f1";
        
        # Platform-specific module
        unityModule = if pkgs.stdenv.isDarwin 
          then "--module mac-mono" 
          else "--module linux-il2cpp";

        # Graphics libraries and runtime dependencies
        runtimeLibs = with pkgs; [
          # Graphics
          libGL
          libGLU
          vulkan-loader
          
          # X11
          xorg.libX11
          xorg.libXcursor
          xorg.libXinerama
          xorg.libXrandr
          xorg.libXi
          xorg.libXext
          xorg.libXfixes
          xorg.libXrender
          xorg.libXcomposite
          xorg.libXdamage
          
          # Audio
          alsa-lib
          libpulseaudio
          
          # System and UI
          gtk3
          glib
          icu
          zlib
          
          # Additional runtime deps
          libglvnd
          libdrm
          mesa
          mesa.drivers
          
          # Unity specific
          udev
          systemd
        ];

        # Debug tools
        debugTools = with pkgs; [
          strace
          ltrace
          binutils  # for readelf
        ];

        # macOS specific tools
        darwinTools = with pkgs; [
          darwin.apple_sdk.frameworks.CoreServices
          darwin.cctools  # Provides install_name_tool
        ];
      in
      with pkgs;    
      {
        devShell = mkShell {
          UNITY_VERSION = "${unityVersion}${changeset}";
          buildInputs = [
            unityhub
            (import ./python.nix { python = python311; })
            autoPatchelfHook
            patchelf
          ] ++ debugTools
          ++ (if stdenv.isDarwin then darwinTools else runtimeLibs);

          shellHook = ''
            echo "Unity development environment ready"
            
            # Set up runtime environment
            export LD_LIBRARY_PATH=${lib.makeLibraryPath runtimeLibs}:$LD_LIBRARY_PATH
            
            # Unity specific environment variables
            export UNITY_ENABLE_GRAPHICS=1
            export UNITY_ENABLE_AUDIO=1
            
            # GTK environment setup
            export XDG_DATA_DIRS=${gsettings-desktop-schemas}/share/gsettings-schemas/${gsettings-desktop-schemas.name}:${gtk3}/share/gsettings-schemas/${gtk3.name}:$XDG_DATA_DIRS
            
            # Export library paths for autopatchelf
            export AUTO_PATCHELF_LIBS=${lib.makeLibraryPath runtimeLibs}
            
            echo "\nInstalling Unity ${unityVersion} with platform support if not present..."
            unityhub -- --headless install --version ${unityVersion} ${unityModule} --changeset ${changeset} 2>/dev/null || true

            chmod +x buildScript.sh

            # Debug helper functions
            check_binary() {
              echo "Checking binary dependencies..."
              ldd ./Builds/Sim.x86_64
              echo "\nChecking for missing symbols..."
              ldd -r ./Builds/Sim.x86_64
            }

            trace_run() {
              echo "Running with strace..."
              strace -f ./Builds/Sim.x86_64 2>strace.log
            }

            debug_libs() {
              echo "Debugging library loading..."
              LD_DEBUG=libs,files ./Builds/Sim.x86_64 2>libs_debug.log
            }
          '';
        };
      }
    );
}
