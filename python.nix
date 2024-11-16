{ python }: with python; with python.pkgs;
let 
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
      grpcio
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
in python.withPackages (ps: [
    matplotlib
    numpy
    nptyping
    mlagents
  ])
