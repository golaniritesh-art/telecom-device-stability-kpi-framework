*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Validate LTE Attach Success Rate
    ${rate}=    Get Lte Attach Success Rate
    Should Be True    ${rate} >= 1
