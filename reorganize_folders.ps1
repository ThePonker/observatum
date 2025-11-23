# OBSERVATUM FOLDER REORGANIZATION SCRIPT
# Date: 23 November 2025
# Run this from the Observatum FV project root folder

Write-Host "🚀 OBSERVATUM FOLDER REORGANIZATION" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Phase A: Create new folders
Write-Host "📁 Phase A: Creating new folders..." -ForegroundColor Yellow

$folders = @(
    "database\handlers",
    "database\queries",
    "widgets\forms",
    "widgets\tables",
    "widgets\panels",
    "utils\submission",
    "utils\validation"
)

foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "  ✅ Created: $folder" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  Already exists: $folder" -ForegroundColor Gray
    }
}

Write-Host ""

# Phase B: Create __init__.py files
Write-Host "📝 Phase B: Creating __init__.py files..." -ForegroundColor Yellow

# database/handlers/__init__.py
$content = @"
""\"UKSI database handlers""\"
from .uksi_handler import UKSIHandler
from .uksi_search import UKSISearch
from .uksi_ranker import UKSIRanker

__all__ = ['UKSIHandler', 'UKSISearch', 'UKSIRanker']
"@
Set-Content -Path "database\handlers\__init__.py" -Value $content
Write-Host "  ✅ Created: database\handlers\__init__.py" -ForegroundColor Green

# database/queries/__init__.py
$content = @"
""\"Database query builders""\"
from .record_query_builder import RecordQueryBuilder

__all__ = ['RecordQueryBuilder']
"@
Set-Content -Path "database\queries\__init__.py" -Value $content
Write-Host "  ✅ Created: database\queries\__init__.py" -ForegroundColor Green

# widgets/forms/__init__.py
$content = @"
""\"Form widgets""\"
from .add_record_widget import AddRecordWidget
from .species_search_widget import SpeciesSearchWidget
from .record_form_builder import RecordFormBuilder

__all__ = ['AddRecordWidget', 'SpeciesSearchWidget', 'RecordFormBuilder']
"@
Set-Content -Path "widgets\forms\__init__.py" -Value $content
Write-Host "  ✅ Created: widgets\forms\__init__.py" -ForegroundColor Green

# widgets/tables/__init__.py
$content = @"
""\"Table widgets""\"
from .record_table_widget import RecordTableWidget

__all__ = ['RecordTableWidget']
"@
Set-Content -Path "widgets\tables\__init__.py" -Value $content
Write-Host "  ✅ Created: widgets\tables\__init__.py" -ForegroundColor Green

# widgets/panels/__init__.py
$content = @"
""\"Panel widgets""\"
from .filter_panel import FilterPanel
from .button_bar import ButtonBar

__all__ = ['FilterPanel', 'ButtonBar']
"@
Set-Content -Path "widgets\panels\__init__.py" -Value $content
Write-Host "  ✅ Created: widgets\panels\__init__.py" -ForegroundColor Green

# utils/submission/__init__.py
$content = @"
""\"Record submission utilities""\"
from .record_submission_handler import RecordSubmissionHandler

__all__ = ['RecordSubmissionHandler']
"@
Set-Content -Path "utils\submission\__init__.py" -Value $content
Write-Host "  ✅ Created: utils\submission\__init__.py" -ForegroundColor Green

# utils/validation/__init__.py
$content = @"
""\"Validation utilities""\"
from .validators import GridReferenceValidator

__all__ = ['GridReferenceValidator']
"@
Set-Content -Path "utils\validation\__init__.py" -Value $content
Write-Host "  ✅ Created: utils\validation\__init__.py" -ForegroundColor Green

Write-Host ""

# Phase C: Move database files
Write-Host "🔄 Phase C: Moving database files..." -ForegroundColor Yellow

# Move record_query_builder.py
if (Test-Path "database\record_query_builder.py") {
    Move-Item -Path "database\record_query_builder.py" -Destination "database\queries\record_query_builder.py" -Force
    Write-Host "  ✅ Moved: record_query_builder.py → database\queries\" -ForegroundColor Green
}

Write-Host "  ⚠️  NOTE: New uksi_*.py files must be downloaded and placed manually" -ForegroundColor Yellow
Write-Host "  📥 Download: uksi_handler.py, uksi_search.py, uksi_ranker.py" -ForegroundColor Yellow
Write-Host "  📍 Place in: database\handlers\" -ForegroundColor Yellow

Write-Host ""

# Phase D: Move widget files
Write-Host "🔄 Phase D: Moving widget files..." -ForegroundColor Yellow

$widgetMoves = @{
    "widgets\add_record_widget.py" = "widgets\forms\add_record_widget.py"
    "widgets\species_search_widget.py" = "widgets\forms\species_search_widget.py"
    "widgets\record_form_builder.py" = "widgets\forms\record_form_builder.py"
    "widgets\record_table_widget.py" = "widgets\tables\record_table_widget.py"
    "widgets\filter_panel.py" = "widgets\panels\filter_panel.py"
    "widgets\button_bar.py" = "widgets\panels\button_bar.py"
}

foreach ($move in $widgetMoves.GetEnumerator()) {
    if (Test-Path $move.Key) {
        Move-Item -Path $move.Key -Destination $move.Value -Force
        $filename = Split-Path $move.Key -Leaf
        $dest = Split-Path $move.Value -Parent
        Write-Host "  ✅ Moved: $filename → $dest\" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  Not found: $($move.Key)" -ForegroundColor Gray
    }
}

Write-Host ""

# Phase E: Move utils files
Write-Host "🔄 Phase E: Moving utils files..." -ForegroundColor Yellow

$utilsMoves = @{
    "utils\record_submission_handler.py" = "utils\submission\record_submission_handler.py"
    "utils\validators.py" = "utils\validation\validators.py"
}

foreach ($move in $utilsMoves.GetEnumerator()) {
    if (Test-Path $move.Key) {
        Move-Item -Path $move.Key -Destination $move.Value -Force
        $filename = Split-Path $move.Key -Leaf
        $dest = Split-Path $move.Value -Parent
        Write-Host "  ✅ Moved: $filename → $dest\" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  Not found: $($move.Key)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "✅ PHASE 1 COMPLETE: Folders created and files moved!" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Download uksi_handler.py, uksi_search.py, uksi_ranker.py" -ForegroundColor White
Write-Host "  2. Place them in database\handlers\" -ForegroundColor White
Write-Host "  3. Run the import update script (coming next)" -ForegroundColor White
Write-Host ""