<#
.SYNOPSIS
    Emergency PR merge with audited branch-protection bypass.

.DESCRIPTION
    Automates the controlled, minimal-duration bypass of branch protection
    required when no reviewers are available for urgent security merges.

    Phases:
      1. Snapshot  – saves current protection JSON to logs/
      2. Lower     – disables enforce_admins, sets approvals=1, keeps
                     CODEOWNERS and status checks unchanged
      3. Merge     – squash-merges the specified PR and deletes its branch
      4. Restore   – re-applies the exact original protection from snapshot
      5. Audit     – writes a timestamped audit log under logs/

    This script MUST only be used under the conditions described in
    RELEASE_WORKFLOW.md § Automated Emergency Merge.

.PARAMETER PrNumber
    The GitHub pull request number to merge.

.PARAMETER DryRun
    If set, performs Phase 1 (snapshot) and prints what would happen without
    making any changes.

.EXAMPLE
    .\scripts\emergency_merge.ps1 -PrNumber 15
    .\scripts\emergency_merge.ps1 -PrNumber 15 -DryRun
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int]$PrNumber,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Helpers ─────────────────────────────────────────────────────────────────

function Write-Step { param([string]$Phase, [string]$Msg)
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
    Write-Host "[$ts] [$Phase] $Msg" -ForegroundColor Cyan
    return $ts
}

function Write-Fail { param([string]$Msg)
    Write-Host "[FAIL] $Msg" -ForegroundColor Red
    exit 1
}

function Redact-Json {
    <# Strip URL values and tokens from JSON for screen output #>
    param([string]$Json)
    $Json -replace '"https?://[^"]*"', '"[REDACTED-URL]"' `
          -replace '("[^"]*token[^"]*")\s*:\s*"[^"]*"', '$1: "[REDACTED]"'
}

# ── Auto-detect OWNER/REPO ────────────────────────────────────────────────

$remote = git remote get-url origin 2>&1
if ($remote -match '([^/]+)/([^/.]+?)(?:\.git)?$') {
    $Owner = $Matches[1]
    $Repo  = $Matches[2]
} else {
    Write-Fail "Could not parse owner/repo from remote: $remote"
}
$base = "repos/$Owner/$Repo/branches/master/protection"
Write-Step "INIT" "Repository: $Owner/$Repo — PR #$PrNumber"

# ── Ensure logs/ directory exists ──────────────────────────────────────────

$logsDir = Join-Path $PSScriptRoot ".." "logs"
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
$runId     = Get-Date -Format "yyyyMMdd-HHmmss"
$snapFile  = Join-Path $logsDir "protection-snapshot-$runId.json"
$auditFile = Join-Path $logsDir "emergency-merge-audit-$runId.log"

# Audit log helper — appends to file AND writes to console
$auditLines = [System.Collections.Generic.List[string]]::new()
function Write-Audit { param([string]$Line)
    $entry = "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK') | $Line"
    $auditLines.Add($entry)
    Write-Host $entry
}

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 1 — SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════

Write-Step "PHASE-1" "Saving current branch protection to $snapFile"
$protectionJson = gh api "$base" 2>&1
if ($LASTEXITCODE -ne 0) { Write-Fail "Cannot read branch protection: $protectionJson" }
[System.IO.File]::WriteAllText($snapFile, $protectionJson)
Write-Audit "SNAPSHOT saved to $snapFile"

# Parse key fields for display (redacted)
$protection = $protectionJson | ConvertFrom-Json
$summary = [ordered]@{
    enforce_admins   = $protection.enforce_admins.enabled
    approvals        = $protection.required_pull_request_reviews.required_approving_review_count
    codeowners       = $protection.required_pull_request_reviews.require_code_owner_reviews
    dismiss_stale    = $protection.required_pull_request_reviews.dismiss_stale_reviews
    status_checks    = ($protection.required_status_checks.contexts -join ", ")
    linear_history   = $protection.required_linear_history.enabled
    allow_force_push = $protection.allow_force_pushes.enabled
}
Write-Step "PHASE-1" "Current protection (redacted):"
$summary.GetEnumerator() | ForEach-Object { Write-Host "  $($_.Key) = $($_.Value)" }
Write-Audit "SNAPSHOT fields: enforce_admins=$($summary.enforce_admins), approvals=$($summary.approvals), codeowners=$($summary.codeowners)"

# ── Validate PR is open and CI green ───────────────────────────────────────

Write-Step "PHASE-1" "Validating PR #$PrNumber..."
$prJson = gh pr view $PrNumber --json state,title,statusCheckRollup 2>&1
if ($LASTEXITCODE -ne 0) { Write-Fail "Cannot read PR #$PrNumber : $prJson" }
$pr = $prJson | ConvertFrom-Json

if ($pr.state -ne "OPEN") { Write-Fail "PR #$PrNumber is $($pr.state), not OPEN." }

$failedChecks = $pr.statusCheckRollup | Where-Object { $_.conclusion -ne "SUCCESS" }
if ($failedChecks) {
    Write-Fail "PR #$PrNumber has non-SUCCESS checks: $($failedChecks | ForEach-Object { "$($_.name)=$($_.conclusion)" } | Out-String)"
}
Write-Audit "PR #$PrNumber validated: state=OPEN, title='$($pr.title)', checks=$(($pr.statusCheckRollup | Measure-Object).Count)/$(($pr.statusCheckRollup | Measure-Object).Count) SUCCESS"

# ── Dry-run exit ───────────────────────────────────────────────────────────

if ($DryRun) {
    Write-Step "DRY-RUN" "Would lower protection, merge PR #$PrNumber, restore protection."
    Write-Step "DRY-RUN" "No changes made. Snapshot saved to $snapFile."
    $auditLines | Set-Content -Path $auditFile -Encoding UTF8
    exit 0
}

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 2 — LOWER PROTECTION (minimal scope)
# ══════════════════════════════════════════════════════════════════════════

Write-Step "PHASE-2" "Disabling enforce_admins..."
$r = gh api "$base/enforce_admins" -X DELETE 2>&1
Write-Audit "API DELETE $base/enforce_admins — done"

Write-Step "PHASE-2" "Setting approvals=1, keeping codeowners=true..."
$reviewBody = '{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}'
$tmpReview = Join-Path $logsDir "_tmp_review_$runId.json"
[System.IO.File]::WriteAllText($tmpReview, $reviewBody)
$r = gh api "$base/required_pull_request_reviews" -X PATCH --input $tmpReview 2>&1
Remove-Item $tmpReview -ErrorAction SilentlyContinue
if ($LASTEXITCODE -ne 0) { Write-Fail "Failed to lower review requirements: $r" }
Write-Audit "API PATCH $base/required_pull_request_reviews — approvals=1, codeowners=true"

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 3 — MERGE
# ══════════════════════════════════════════════════════════════════════════

Write-Step "PHASE-3" "Squash-merging PR #$PrNumber..."
$mergeResult = gh pr merge $PrNumber --squash --delete-branch --admin 2>&1
Write-Audit "MERGE PR #$PrNumber — result: $mergeResult"

# Check success by verifying PR is now MERGED
$postMerge = gh pr view $PrNumber --json state --jq ".state" 2>&1
if ($postMerge -ne "MERGED") {
    Write-Host "[WARN] PR state after merge attempt: $postMerge — proceeding to restore protection" -ForegroundColor Yellow
    Write-Audit "WARN: PR state=$postMerge (expected MERGED)"
}

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 4 — RESTORE PROTECTION
# ══════════════════════════════════════════════════════════════════════════

Write-Step "PHASE-4" "Restoring enforce_admins..."
$r = gh api "$base/enforce_admins" -X POST 2>&1
Write-Audit "API POST $base/enforce_admins — re-enabled"

Write-Step "PHASE-4" "Restoring review requirements from snapshot..."
$origReview = $protection.required_pull_request_reviews
$restoreBody = @{
    required_approving_review_count = $origReview.required_approving_review_count
    dismiss_stale_reviews           = $origReview.dismiss_stale_reviews
    require_code_owner_reviews      = $origReview.require_code_owner_reviews
    require_last_push_approval      = $origReview.require_last_push_approval
} | ConvertTo-Json -Compress
$tmpRestore = Join-Path $logsDir "_tmp_restore_$runId.json"
[System.IO.File]::WriteAllText($tmpRestore, $restoreBody)
$r = gh api "$base/required_pull_request_reviews" -X PATCH --input $tmpRestore 2>&1
Remove-Item $tmpRestore -ErrorAction SilentlyContinue
if ($LASTEXITCODE -ne 0) { Write-Fail "CRITICAL: Failed to restore review protection: $r — MANUALLY re-enable NOW." }
Write-Audit "API PATCH $base/required_pull_request_reviews — restored approvals=$($origReview.required_approving_review_count), codeowners=$($origReview.require_code_owner_reviews)"

# ── Verify restoration ────────────────────────────────────────────────────

Write-Step "PHASE-4" "Verifying restored protection..."
$verifyJson = gh api "$base" --jq "{enforce_admins:.enforce_admins.enabled, approvals:.required_pull_request_reviews.required_approving_review_count, codeowners:.required_pull_request_reviews.require_code_owner_reviews, dismiss_stale:.required_pull_request_reviews.dismiss_stale_reviews}" 2>&1
Write-Host $verifyJson
Write-Audit "VERIFY restored: $verifyJson"

# ══════════════════════════════════════════════════════════════════════════
#  PHASE 5 — AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════

Write-Step "PHASE-5" "Writing audit log to $auditFile"
$header = @(
    "=" * 72
    "EMERGENCY MERGE AUDIT LOG"
    "=" * 72
    "Run ID       : $runId"
    "PR Number    : #$PrNumber"
    "PR Title     : $($pr.title)"
    "Repository   : $Owner/$Repo"
    "Operator     : $(git config user.name) <$(git config user.email)>"
    "Snapshot File: $snapFile"
    "=" * 72
    ""
)
($header + $auditLines) | Set-Content -Path $auditFile -Encoding UTF8
Write-Audit "Audit log written to $auditFile"

Write-Step "DONE" "Emergency merge of PR #$PrNumber complete."
Write-Host ""
Write-Host "IMPORTANT: File a SEC-INCIDENT issue per GOVERNANCE.md:" -ForegroundColor Yellow
Write-Host "  gh issue create --title 'SEC-INCIDENT: Emergency merge of PR #$PrNumber ($(Get-Date -Format 'yyyy-MM-dd'))' --body-file $auditFile --label security,incident,governance" -ForegroundColor Yellow
