*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Validate 5G Registration Success Rate
    ${rate}=    Get 5g Registration Success Rate
    Should Be True    ${rate} >= 1
