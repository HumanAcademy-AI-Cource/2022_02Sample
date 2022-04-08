cmake_minimum_required(VERSION 3.0.2)
project(aws_demokit)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  message_generation
)

add_service_files(
  FILES
  SceneRekognition.srv
)

generate_messages(DEPENDENCIES
  std_msgs
  sensor_msgs
)

catkin_package(
  CATKIN_DEPENDS
  message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)