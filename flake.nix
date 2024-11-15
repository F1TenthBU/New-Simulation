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
        
        # Get architecture
        arch = if system == "x86_64-linux" then "x86_64"
          else if system == "aarch64-linux" then "arm64"
          else if system == "x86_64-darwin" then "x64"
          else if system == "aarch64-darwin" then "arm64"
          else throw "Unsupported system: ${system}";
        
        # Platform-specific module
        unityModule = if pkgs.stdenv.isDarwin 
          then "--module mac-il2cpp"
          else "--module linux-il2cpp";

        # Platform-specific Unity Hub command
        unityHubCmd = if pkgs.stdenv.isDarwin
          then "/Applications/Unity\\ Hub.app/Contents/MacOS/Unity\\ Hub"
          else "${pkgs.unityhub}/bin/unityhub";

        # Linux-specific libraries
        linuxLibs = with pkgs; [
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

          unityhub
          
          # System
          glib
          icu
          systemd
        ];

        # macOS-specific libraries and tools
        macLibs = with pkgs; [
          darwin.apple_sdk.frameworks.CoreServices
          darwin.cctools  # For install_name_tool
        ];

        # Common libraries for both platforms
        commonLibs = with pkgs; [
          zlib
        ];

      in
      with pkgs;    
      {
        devShell = mkShell {
          UNITY_VERSION = "${unityVersion}${changeset}";
          buildInputs = [
            (import ./python.nix { python = python311; })
            autoPatchelfHook
            patchelf
          ] ++ commonLibs
          ++ (if stdenv.isDarwin then macLibs else linuxLibs);

          shellHook = ''
            # Set up Unity Hub command
            unityhub() {
              ${unityHubCmd} "$@"
            }
            
            echo "Unity development environment ready"
            echo "Architecture: ${arch}"
            
            ${if !stdenv.isDarwin then ''
              # Linux-specific environment setup
              export LD_LIBRARY_PATH=${lib.makeLibraryPath (linuxLibs ++ commonLibs)}:$LD_LIBRARY_PATH
              export XDG_DATA_DIRS=${gsettings-desktop-schemas}/share/gsettings-schemas/${gsettings-desktop-schemas.name}:${gtk3}/share/gsettings-schemas/${gtk3.name}:$XDG_DATA_DIRS
              export AUTO_PATCHELF_LIBS=${lib.makeLibraryPath (linuxLibs ++ commonLibs)}
              echo "Installing Unity ${unityVersion} with platform support if not present..."
              unityhub -- --headless install --version ${unityVersion} --changeset ${changeset} --architecture ${arch} ${unityModule}
            '' else ''
              echo "Install the right version of Unity manually, the one I assume you use is ${unityVersion}"
            ''}
          '';
        };
      }
    );
}
