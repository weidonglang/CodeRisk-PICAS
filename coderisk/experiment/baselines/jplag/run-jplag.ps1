param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$JplagArguments
)

$ErrorActionPreference = "Stop"

if (-not $env:JPLAG_JAR) {
    throw "JPLAG_JAR is not set. See experiment/baselines/jplag/README.md."
}
if (-not (Test-Path -LiteralPath $env:JPLAG_JAR -PathType Leaf)) {
    throw "JPLAG_JAR does not point to an existing file: $env:JPLAG_JAR"
}

$java = if ($env:JPLAG_JAVA) { $env:JPLAG_JAVA } else { "java" }
if ($env:JPLAG_JAVA -and -not (Test-Path -LiteralPath $java -PathType Leaf)) {
    throw "JPLAG_JAVA does not point to an existing executable: $java"
}

& $java -jar $env:JPLAG_JAR @JplagArguments
exit $LASTEXITCODE
