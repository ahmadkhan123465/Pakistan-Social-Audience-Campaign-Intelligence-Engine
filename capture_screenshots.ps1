$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$outDir = "C:\Users\Kashif Hafeez\Desktop\pak-audience-intel-main\docs\screenshots"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$pages = @(
    @{ name = "01_executive_dashboard.png"; url = "http://127.0.0.1:5000/" },
    @{ name = "02_ad_budget_optimizer.png"; url = "http://127.0.0.1:5000/budget" },
    @{ name = "03_youtube_sentiment_intel.png"; url = "http://127.0.0.1:5000/youtube" },
    @{ name = "04_database_and_sql_console.png"; url = "http://127.0.0.1:5000/database" },
    @{ name = "05_comments_table_b.png"; url = "http://127.0.0.1:5000/comments" },
    @{ name = "06_posts_table_a.png"; url = "http://127.0.0.1:5000/posts" },
    @{ name = "07_nlp_classifier_sandbox.png"; url = "http://127.0.0.1:5000/analyze" },
    @{ name = "08_audience_segments.png"; url = "http://127.0.0.1:5000/segments" },
    @{ name = "09_anomaly_detection.png"; url = "http://127.0.0.1:5000/anomalies" },
    @{ name = "10_strategic_recommendations.png"; url = "http://127.0.0.1:5000/recommendations" }
)

foreach ($p in $pages) {
    $target = Join-Path $outDir $p.name
    Write-Host "Capturing $($p.name) from $($p.url) ..."
    $proc = Start-Process -FilePath $edge -ArgumentList "--headless", "--disable-gpu", "--window-size=1400,900", "--screenshot=""$target""", "$($p.url)" -PassThru -Wait
    Start-Sleep -Milliseconds 600
}

Write-Host "All screenshots captured successfully!"
Get-ChildItem $outDir
