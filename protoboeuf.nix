{ buildPythonPackage
, fetchurl
, lib
}:

buildPythonPackage rec {
  pname = "protobuf";
  version = "3.19.6";
  format = "wheel";

  src = fetchurl {
    url = "https://files.pythonhosted.org/packages/32/27/1141a8232723dcb10a595cc0ce4321dcbbd5215300bf4acfc142343205bf/protobuf-3.19.6-py2.py3-none-any.whl";
    sha256 = "sha256-FAgkV9wCvpRvYLFarTXp9caec4+A67wJAKGbyDc0paQ=";
  };

  # Wheels don't need build inputs
  doCheck = false;

  pythonImportsCheck = [ "google.protobuf" ];

  meta = with lib; {
    description = "Protocol Buffers are Google's data interchange format";
    homepage = "https://developers.google.com/protocol-buffers/";
    license = licenses.bsd3;
  };
}