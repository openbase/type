# Openbase Protobuf Type Lib

This is a open source type library based on [google protocol buffers](https://developers.google.com/protocol-buffers).

Currently we support the generation of java and c++ types via our build tools.
Python type are supported soon.

## How to generate the Java Types

Building the javatypes is simple because the maven build tool is even downloading the protobuf binaries related to your os.
To generate the java types just execute
```
mvn install
```
afterwars all java types are bundled in jar placed at target/type-x.x.x.jar

## How to generate the C++ Types

### Build tool installation

The c++ types are generated the build tool cmake. Those and the protobuf-dev library needs to be installed first.

#### Mac Os
```
brew install protobuf cmake
```
#### Debian based distribution
```
sudo apt install libprotobuf-dev protobuf-compiler cmake
```

### Generate
Now you are ready the generate the c++ tyes. First of all we need a build folder ```mkdir build```.
Let's tell cmake to generate the ```makefile``` which can than be used to build the types by calling ```make```.
```
mkdir build
cd build
cmake ..
make
```
