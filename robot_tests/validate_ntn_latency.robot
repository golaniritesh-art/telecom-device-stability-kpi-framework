*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Validate NTN Latency Threshold
    ${latency}=    Get Ntn Average Latency
    Should Be True    ${latency} < 250
