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
        
        # Runtime libraries
        runtimeLibs = with pkgs; if stdenv.isDarwin then [
          darwin.apple_sdk.frameworks.CoreServices
          darwin.cctools
        ] else [
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
          unityhub
        ];

      in
      with pkgs;    
      {
        devShell = mkShell {
          buildInputs = [
            (import ./python.nix { python = python311; })
            autoPatchelfHook
            patchelf
            zlib
          ] ++ runtimeLibs;

          shellHook =
            if !stdenv.isDarwin then ''
              export LD_LIBRARY_PATH=${lib.makeLibraryPath runtimeLibs}:$LD_LIBRARY_PATH
              export AUTO_PATCHELF_LIBS=${lib.makeLibraryPath runtimeLibs}
            ''
            else "";
        };
      }
    );
}
