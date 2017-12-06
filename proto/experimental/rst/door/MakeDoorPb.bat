//@echo off
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST LockStatus.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST ContactStatus.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST KnockStatus.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST RadarStatus.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST SpeakerStatus.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST MotorStatus.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST DoorStatus.proto

protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST LockControl.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST SpeakerControl.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST MotorControl.proto
protoc --nanopb_out=C:\Users\kemper_b\Documents\Arduino\libraries\RST DoorControl.proto