*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Validate Handover Success Rate
    ${rate}=    Get Handover Success Rate
    Should Be True    ${rate} >= 40
