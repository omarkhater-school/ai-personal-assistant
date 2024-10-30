# run-tests.ps1

# Clear the terminal for readability
Clear-Host

# Define the project root as PYTHONPATH to resolve module paths
$projectRoot = "D:\projects\ai-personal-assistant"
$env:PYTHONPATH = $projectRoot

# Define directories for the tests
$unitTestsDir = "tests/unit"
$acceptanceTestsDir = "tests/acceptance"
$integrationTestsDir = "tests/integeration"
$coverageReportDir = "coverage_report"

# Create the coverage report directory if it doesn't exist
if (!(Test-Path -Path $coverageReportDir)) {
    New-Item -ItemType Directory -Path $coverageReportDir | Out-Null
}

# Define the log file path
$logFilePath = ".\logs\test_run.log"

# Clear the log file at the start of the script
Clear-Content -Path $logFilePath

# Run Unit Tests with Coverage
Write-Output "Running Unit Tests with Coverage..." | Tee-Object -FilePath $logFilePath -Append
$coverageOutput = pytest $unitTestsDir --cov=. --cov-report term-missing --cov-report html:$coverageReportDir/html 2>&1 | Tee-Object -FilePath $logFilePath -Append

if ($LASTEXITCODE -eq 0) {
    Write-Output "Unit Tests Passed!" | Tee-Object -FilePath $logFilePath -Append
    $unitTestsPassed = $true
} else {
    Write-Output "Unit Tests Failed." | Tee-Object -FilePath $logFilePath -Append
    $unitTestsPassed = $false
}

# Extract coverage percentage from the output
$coveragePercentage = ($coverageOutput | Select-String -Pattern 'TOTAL.*?(\d+)%' | ForEach-Object {
    if ($_ -match 'TOTAL.*?(\d+)%') {
        return [int]$matches[1]
    }
}).ToString()

if ($coveragePercentage -eq $null) {
    $coveragePercentage = "No data"
} else {
    $coveragePercentage += "%"
}

# Run Acceptance Tests without Coverage
Write-Output "Running Acceptance Tests..." | Tee-Object -FilePath $logFilePath -Append
$acceptanceTestResult = pytest $acceptanceTestsDir 2>&1 | Tee-Object -FilePath $logFilePath -Append
if ($LASTEXITCODE -eq 0) {
    Write-Output "Acceptance Tests Passed!" | Tee-Object -FilePath $logFilePath -Append
    $acceptanceTestsPassed = $true
} else {
    Write-Output "Acceptance Tests Failed." | Tee-Object -FilePath $logFilePath -Append
    $acceptanceTestsPassed = $false
}

# Run Integration Tests
Write-Output "Running Integration Tests..." | Tee-Object -FilePath $logFilePath -Append
$integrationTestResult = pytest $integrationTestsDir 2>&1 | Tee-Object -FilePath $logFilePath -Append
if ($LASTEXITCODE -eq 0) {
    Write-Output "Integration Tests Passed!" | Tee-Object -FilePath $logFilePath -Append
    $integrationTestsPassed = $true
} else {
    Write-Output "Integration Tests Failed." | Tee-Object -FilePath $logFilePath -Append
    $integrationTestsPassed = $false
}

# Summary Output
Write-Output "`nSummary:" | Tee-Object -FilePath $logFilePath -Append
Write-Output "----------------------" | Tee-Object -FilePath $logFilePath -Append
Write-Output ("Unit Tests: " + ($(if ($unitTestsPassed) { "Passed" } else { "Failed" }))) | Tee-Object -FilePath $logFilePath -Append
Write-Output ("Acceptance Tests: " + ($(if ($acceptanceTestsPassed) { "Passed" } else { "Failed" }))) | Tee-Object -FilePath $logFilePath -Append
Write-Output ("Integration Tests: " + ($(if ($integrationTestsPassed) { "Passed" } else { "Failed" }))) | Tee-Object -FilePath $logFilePath -Append
Write-Output ("Test Coverage: " + $coveragePercentage) | Tee-Object -FilePath $logFilePath -Append

if ($unitTestsPassed -and $acceptanceTestsPassed -and $integrationTestsPassed) {
    Write-Output "`nAll tests passed successfully!" | Tee-Object -FilePath $logFilePath -Append
} else {
    Write-Output "`nSome tests failed. Please check the details above." | Tee-Object -FilePath $logFilePath -Append
}
