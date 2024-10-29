# run-tests.ps1

# Clear the terminal for readability
Clear-Host

# Define the project root as PYTHONPATH to resolve module paths
$projectRoot = "D:\projects\ai-personal-assistant"
$env:PYTHONPATH = $projectRoot

# Define directories for the tests
$unitTestsDir = "tests/unit"
$acceptanceTestsDir = "tests/acceptance"
$coverageReportDir = "coverage_report"

# Create the coverage report directory if it doesn't exist
if (!(Test-Path -Path $coverageReportDir)) {
    New-Item -ItemType Directory -Path $coverageReportDir | Out-Null
}

# Run Unit Tests with Coverage
Write-Output "Running Unit Tests with Coverage..."
$coverageOutput = pytest $unitTestsDir --cov=. --cov-report term-missing --cov-report html:$coverageReportDir/html

if ($LASTEXITCODE -eq 0) {
    Write-Output "Unit Tests Passed!"
    $unitTestsPassed = $true
} else {
    Write-Output "Unit Tests Failed."
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

# Run Acceptance Tests without Coverage (acceptance tests usually don't require coverage)
Write-Output "Running Acceptance Tests..."
$acceptanceTestResult = pytest $acceptanceTestsDir
if ($LASTEXITCODE -eq 0) {
    Write-Output "Acceptance Tests Passed!"
    $acceptanceTestsPassed = $true
} else {
    Write-Output "Acceptance Tests Failed."
    $acceptanceTestsPassed = $false
}

# Summary Output
Write-Output "`nSummary:"
Write-Output "----------------------"
Write-Output ("Unit Tests: " + ($(if ($unitTestsPassed) { "Passed" } else { "Failed" })))
Write-Output ("Acceptance Tests: " + ($(if ($acceptanceTestsPassed) { "Passed" } else { "Failed" })))
Write-Output ("Test Coverage: " + $coveragePercentage)

if ($unitTestsPassed -and $acceptanceTestsPassed) {
    Write-Output "`nAll tests passed successfully!"
} else {
    Write-Output "`nSome tests failed. Please check the details above."
}
