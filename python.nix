{ python, pkgs }: with python; with python.pkgs;
let 
  protobuf = python.pkgs.callPackage ./protoboeuf.nix { };
  mlagents_envs = buildPythonPackage rec {
    pname = "mlagents_envs";
    version = "1.1.0";
    format = "wheel";
    
    src = fetchPypi {
      inherit pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      platform = "any";
      sha256 = "sha256-+7flTGMnpT8LfdYV3klBSvSW5fdmzMEPF103MbMruYU=";
    };
    
    propagatedBuildInputs = [
      (grpcio.override { inherit protobuf; })
      h5py
      numpy
      distutils
      protobuf
    ];
    
    doCheck = false;
  };
  mlagents = buildPythonPackage rec {
    pname = "mlagents";
    version = "1.1.0";
    format = "wheel";
    
    src = fetchPypi {
      inherit pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      platform = "any";
      sha256 = "sha256-BnHkD7Tk2odA0Yu85H1aXvHFig250QmEb749mNcStPQ=";
    };
    
    propagatedBuildInputs = [
      mlagents_envs
    ];
    
    doCheck = false;
  };

  wgpu = buildPythonPackage rec {
    pname = "wgpu";
    version = "0.19.0";
    format = "wheel";

    src = fetchPypi {
      inherit pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      abi = "none";
      platform = {
        x86_64-linux = "manylinux_2_28_x86_64";
        aarch64-linux = "manylinux_2_28_aarch64";
        x86_64-darwin = "macosx_10_9_x86_64";
        aarch64-darwin = "macosx_11_0_arm64";
      }.${system};
      hash = {
        x86_64-linux = "sha256-TtVeNyQq5JghPdoUrDgdM7gnAnFDRuIKLDI8xCe7h64=";
        aarch64-linux = "sha256-syxfUZbZqloO7nn9etaCNyXpQv5vTiRhmhlGh7WVkok=";
        x86_64-darwin = "sha256-0Xq1xjUJc4Zh86LRQOLGS7n61BYpi/0ovIUXzSKzwpc=";
        aarch64-darwin = "sha256-CNXF+deGjPAWteG9FTFtk+HzBkM7X15pqeYqa4YrJEQ=";
      }.${system};
    };

    propagatedBuildInputs = [
      cffi
      numpy
      typing-extensions
      glfw
    ] ++ [(if pkgs.stdenv.isDarwin then rubicon-objc else null)];

    doCheck = false;
  };

  gymnasium = buildPythonPackage rec {
    pname = "gymnasium";
    version = "0.28.0";
    format = "wheel";
    src = fetchPypi {
      inherit pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      platform = "any";
      sha256 = "sha256-sxUdXNKRhNXXwJwmBLr8o23zL7nOuuI9q+XnwOuD1eo=";
    };
  };

  pylinalg = buildPythonPackage rec {
    pname = "pylinalg";
    version = "0.4.1";
    format = "wheel";

    src = fetchPypi {
      inherit pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      platform = "any";
      sha256 = "sha256-9RL3rbI26ICODcnT4zVBgMRvc8KNq5zHGD+LR8iygI8=";
    };

    propagatedBuildInputs = [
      numpy
    ];

    doCheck = false;
  };


  pygfx = buildPythonPackage rec {
    pname = "pygfx";
    version = "0.6.0";
    format = "wheel";

    src = fetchPypi {
      inherit pname version;
      format = "wheel";
      dist = "py3";
      python = "py3";
      platform = "any";
      sha256 = "sha256-8RNUOM5tlZasqoACVzy3geb6I0UsPQvLXjbOKu3SB2k=";
    };

    propagatedBuildInputs = [
      pylinalg
      numpy
      (freetype-py.overridePythonAttrs (oldAttrs: {
        version = "2.5.1";
        src = pkgs.fetchFromGitHub {
          owner = "rougier";
          repo = "freetype-py";
          rev = "v2.5.1";
          sha256 = "sha256-lwb9cMKeLd8JIQdiMvFSWH+Wd1L9kmnw5R+7nwwBmjI=";
        };
      }))
      uharfbuzz
      jinja2
      wgpu
    ];

    doCheck = false;
  };

in python.withPackages (ps: [
    matplotlib
    numpy
    nptyping
    mlagents
    wgpu
    gymnasium
    pygfx
  ])
