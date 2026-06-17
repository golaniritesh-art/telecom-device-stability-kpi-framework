*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Validate KPI Failure Count Is Generated
    ${count}=    Get Kpi Failure Count
    Should Be True    ${count} > 0
