# PowerShell script to investigate KEY mismatch between tables
# This is likely why hierarchy extraction doesn't work for all species

$mdbPath = "C:\Users\wjhee\Documents\Digital Luggage\Projects\Observatum\Observatum FV\data\UKSI.mdb"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "UKSI.MDB KEY MISMATCH INVESTIGATION"
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

$connectionString = "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=$mdbPath"
$connection = New-Object System.Data.OleDb.OleDbConnection($connectionString)

try {
    $connection.Open()
    $cmd = $connection.CreateCommand()
    
    # 1. Check table sizes
    Write-Host "📊 TABLE SIZES:" -ForegroundColor Yellow
    Write-Host "-" * 70
    
    $cmd.CommandText = "SELECT COUNT(*) FROM TAXON_LIST_ITEM"
    $tli_count = $cmd.ExecuteScalar()
    Write-Host "   TAXON_LIST_ITEM: $($tli_count.ToString('N0')) records"
    
    $cmd.CommandText = "SELECT COUNT(*) FROM ORGANISM_MASTER"
    $org_count = $cmd.ExecuteScalar()
    Write-Host "   ORGANISM_MASTER: $($org_count.ToString('N0')) records"
    Write-Host ""
    
    # 2. Check specific species
    Write-Host "🔍 CHECKING TEST SPECIES:" -ForegroundColor Yellow
    Write-Host "-" * 70
    
    $testSpecies = @(
        @{Name="Turdus merula"; Common="Blackbird"},
        @{Name="Erithacus rubecula"; Common="Robin"},
        @{Name="Rutpela maculata"; Common="Beetle"}
    )
    
    foreach ($species in $testSpecies) {
        Write-Host ""
        Write-Host "   $($species.Name) ($($species.Common)):" -ForegroundColor Cyan
        Write-Host "   " + ("-" * 65)
        
        # Check TAXON_LIST_ITEM
        $cmd.CommandText = "SELECT TAXON_LIST_ITEM_KEY FROM TAXON_LIST_ITEM WHERE PREFERRED_NAME LIKE '$($species.Name)%'"
        $reader = $cmd.ExecuteReader()
        
        if ($reader.Read()) {
            $tli_key = $reader["TAXON_LIST_ITEM_KEY"]
            Write-Host "   ✅ TAXON_LIST_ITEM_KEY: $tli_key" -ForegroundColor Green
            $reader.Close()
            
            # Check ORGANISM_MASTER with same species name
            $cmd.CommandText = "SELECT TAXON_VERSION_KEY, PARENT_TVK FROM ORGANISM_MASTER WHERE RECOMMENDED_SCIENTIFIC_NAME LIKE '$($species.Name)%'"
            $reader = $cmd.ExecuteReader()
            
            if ($reader.Read()) {
                $org_tvk = $reader["TAXON_VERSION_KEY"]
                $parent = if ($reader.IsDBNull(1)) { "[NULL]" } else { $reader["PARENT_TVK"] }
                Write-Host "   ✅ ORGANISM TAXON_VERSION_KEY: $org_tvk" -ForegroundColor Green
                Write-Host "   ✅ ORGANISM PARENT_TVK: $parent" -ForegroundColor Green
                $reader.Close()
                
                # Compare keys
                if ($tli_key -eq $org_tvk) {
                    Write-Host "   ✅ KEYS MATCH - Hierarchy should work!" -ForegroundColor Green
                } else {
                    Write-Host "   ❌ KEYS DON'T MATCH - Hierarchy will FAIL!" -ForegroundColor Red
                    Write-Host "      TLI uses: $tli_key" -ForegroundColor Red
                    Write-Host "      ORG uses: $org_tvk" -ForegroundColor Red
                }
            } else {
                Write-Host "   ❌ NOT in ORGANISM_MASTER - No hierarchy available!" -ForegroundColor Red
                $reader.Close()
            }
        } else {
            Write-Host "   ❌ NOT in TAXON_LIST_ITEM!" -ForegroundColor Red
            $reader.Close()
        }
    }
    
    Write-Host ""
    Write-Host ""
    Write-Host "🔑 KEY FIELD INVESTIGATION:" -ForegroundColor Yellow
    Write-Host "-" * 70
    
    # Check what key fields exist in TAXON_LIST_ITEM
    $cmd.CommandText = "SELECT TOP 1 * FROM TAXON_LIST_ITEM WHERE PREFERRED_NAME LIKE 'Erithacus rubecula%'"
    $reader = $cmd.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "   KEY FIELDS in TAXON_LIST_ITEM (Robin):"
        for ($i = 0; $i -lt $reader.FieldCount; $i++) {
            $colName = $reader.GetName($i)
            if ($colName -match "KEY|TVK|VERSION") {
                $value = if ($reader.IsDBNull($i)) { "[NULL]" } else { $reader.GetValue($i) }
                Write-Host "      • $colName = $value" -ForegroundColor Yellow
            }
        }
    }
    $reader.Close()
    Write-Host ""
    
    # Check ORGANISM_MASTER
    $cmd.CommandText = "SELECT TOP 1 * FROM ORGANISM_MASTER WHERE RECOMMENDED_SCIENTIFIC_NAME LIKE 'Erithacus rubecula%'"
    $reader = $cmd.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "   KEY FIELDS in ORGANISM_MASTER (Robin):"
        for ($i = 0; $i -lt $reader.FieldCount; $i++) {
            $colName = $reader.GetName($i)
            if ($colName -match "KEY|TVK|VERSION") {
                $value = if ($reader.IsDBNull($i)) { "[NULL]" } else { $reader.GetValue($i) }
                Write-Host "      • $colName = $value" -ForegroundColor Yellow
            }
        }
    }
    $reader.Close()
    Write-Host ""
    
    Write-Host ""
    Write-Host "💡 SOLUTION:" -ForegroundColor Green
    Write-Host "-" * 70
    Write-Host "   If keys don't match, uksi_extractor.py needs to:"
    Write-Host "   1. Extract hierarchy from TAXON_LIST_ITEM.PARENT field"
    Write-Host "      (not from ORGANISM_MASTER)"
    Write-Host "   OR"
    Write-Host "   2. Map between TAXON_LIST_ITEM_KEY and TAXON_VERSION_KEY"
    Write-Host "      when building hierarchy table"
    Write-Host ""
    
} catch {
    Write-Host "❌ ERROR: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    if ($connection.State -eq 'Open') {
        $connection.Close()
    }
}

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "INVESTIGATION COMPLETE"
Write-Host "=" * 70 -ForegroundColor Cyan
