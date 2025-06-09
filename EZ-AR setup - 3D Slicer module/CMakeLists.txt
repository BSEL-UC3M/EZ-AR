cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(AR_HoloLens_QRtracking)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/AR_HoloLens_QRtracking")
set(EXTENSION_CATEGORY "AR")
set(EXTENSION_CONTRIBUTORS "Alicia Pose (UC3M), Gemma Arce (UC3M)")
set(EXTENSION_DESCRIPTION "Módulo que complementa la app de AR Universal que desarrolló Gemma.")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/AR_HoloLens_QRtracking.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/AR_HoloLens_QRtracking/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(Univ_HoloAR_setup)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
