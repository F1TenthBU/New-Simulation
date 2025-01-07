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
          config = {
            allowUnfree = true;
          };
        };
        
        # Platform-specific settings
        platformSettings = if pkgs.stdenv.isDarwin then {
          libs = with pkgs; [
            darwin.apple_sdk.frameworks.CoreServices
            darwin.cctools
          ];
          setupScript = '''';
        } else {
          libs = with pkgs; [
            xorg.libX11
            xorg.libXcursor
            xorg.libXrandr
            xorg.libXi
            xorg.libXext
            xorg.libxcb
            libxkbcommon
            gtk3
            gdk-pixbuf
            cairo
            pango
            libGL
            glib
            glibc
            icu
            systemd
            zlib
            libxml2
            stdenv.cc.cc.lib  # for libstdc++
            tbb
            ocl-icd  # OpenCL
            openimagedenoise
            qt5.qtbase
            qt5.qtx11extras
            wayland
            fontconfig
            freetype
            lttng-ust
            dbus
          ];
          setupScript = ''
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath platformSettings.libs}:$LD_LIBRARY_PATH
            export RUNTIME_DEPS="${pkgs.lib.makeLibraryPath platformSettings.libs}"
          '';
        };

      in
      with pkgs;    
      {
        devShell = mkShell {
          buildInputs = [
            (import ./python.nix { python = python310; pkgs = pkgs; })
            autoPatchelfHook
            patchelf
          ] ++ platformSettings.libs;

          shellHook = ''
            echo "Unity development environment ready"
            ${if pkgs.stdenv.isLinux then ''
              ${platformSettings.setupScript}
            '' else ''''}
            # Add python directory to PYTHONPATH
            export PYTHONPATH=$PWD/python:$PYTHONPATH
            chmod +x buildScript.sh
          '';
        };
      }
    );
}
