*** Settings ***
Library    ../robot_libraries/TelecomValidationLibrary.py

*** Test Cases ***
Stable Firmware Dataset Should Stay Healthy
    [Template]    Validate Scenario Dataset
    data/scenarios/stable_firmware_all_pass.csv    stable_firmware    1000    1000    0    0    0    0

Modem Reset Dataset Should Show Device Stability Issue
    [Template]    Validate Scenario Dataset
    data/scenarios/modem_reset_issue.csv    modem_resets    1000    0    300    0    0    0

Network Instability Dataset Should Show RAN And Transport Issues
    [Template]    Validate Scenario Dataset
    data/scenarios/network_instability.csv    network_instability    1000    0    0    100    150    100

*** Keywords ***
Validate Scenario Dataset
    [Arguments]    ${csv_path}    ${scenario_name}    ${min_records}    ${min_pass_count}    ${min_modem_resets}    ${min_network_lost}    ${min_handover_failures}    ${min_call_drops}
    ${summary}=    Summarize Csv Scenario    ${csv_path}
    Should Be True    ${summary}[total_records] >= ${min_records}
    Should Be True    ${summary}[pass_count] >= ${min_pass_count}
    Should Be True    ${summary}[modem_reset_count] >= ${min_modem_resets}
    Should Be True    ${summary}[network_lost_count] >= ${min_network_lost}
    Should Be True    ${summary}[handover_failure_count] >= ${min_handover_failures}
    Should Be True    ${summary}[call_drop_count] >= ${min_call_drops}
