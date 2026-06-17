*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Validate SON Recommendations Generated
    ${count}=    Get Son Recommendation Count
    Should Be True    ${count} > 0
