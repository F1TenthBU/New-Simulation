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
        
        # Platform-specific settings
        platformSettings = if pkgs.stdenv.isDarwin then {
          libs = with pkgs; [
            darwin.apple_sdk.frameworks.CoreServices
            darwin.cctools
          ];
          setupScript = '''';
        } else if pkgs.stdenv.isLinux then {
          libs = with pkgs; [
            xorg.libX11
            xorg.libXcursor
            xorg.libXrandr
            xorg.libXi
            gtk3
            gdk-pixbuf
            cairo
            pango
            libGL
            glib
            icu
            systemd
            zlib
          ];
          setupScript = ''
            export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath platformSettings.libs}:$LD_LIBRARY_PATH
            export RUNTIME_DEPS="${pkgs.lib.makeLibraryPath platformSettings.libs}"
          '';
        } else throw "Unsupported system";

      in
      with pkgs;    
      {
        devShell = mkShell {
          buildInputs = [
            (import ./python.nix { python = python310; })
            autoPatchelfHook
            patchelf
          ] ++ platformSettings.libs;

          shellHook = ''
            echo "Unity development environment ready"
            ${if pkgs.stdenv.isLinux then ''
              ${platformSettings.setupScript}
            '' else ''''}
            chmod +x buildScript.sh
          '';
        };
      }
    );
}
