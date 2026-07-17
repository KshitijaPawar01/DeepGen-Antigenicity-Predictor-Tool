<?php
session_start();

// Check session data
if (!isset($_SESSION['input_path']) || !isset($_SESSION['input_type'])) {
    die("
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Error - DeepGEN</title>
        <style>
            body {
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }
            .error-container {
                background: white;
                padding: 3em;
                border-radius: 24px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 500px;
            }
            .error-icon {
                font-size: 4em;
                margin-bottom: 0.5em;
            }
            h2 { color: #dc2626; margin-bottom: 1em; }
            p { color: #666; margin-bottom: 2em; line-height: 1.6; }
            a {
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                transition: transform 0.3s ease;
            }
            a:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class='error-container'>
            <div class='error-icon'>⚠️</div>
            <h2>No Input Found</h2>
            <p>Please go back and submit a sequence or upload a file to begin prediction.</p>
            <a href='index1.html'>🏠 Return to Home</a>
        </div>
    </body>
    </html>
    ");
}

$input_file = $_SESSION['input_path'];
$input_type = $_SESSION['input_type'];

// Remove from session to avoid reuse
unset($_SESSION['input_path']);
unset($_SESSION['input_type']);

//=======================================================
//          CONFIGURATION - UPDATE THESE PATHS
// =======================================================
$pythonPath = "C:\\Users\\Kshitija\\AppData\\Local\\Programs\\Python\\Python311\\python.exe";
$scriptPath = 'C:\\wamp64\\www\\DeepGEN\\predictor.py';
putenv("PYTHONPATH=C:\\Users\\Kshitija\\AppData\\Roaming\\Python\\Python311\\site-packages");

// =======================================================
//          BUILD AND EXECUTE COMMAND
// =======================================================
$command = sprintf(
    '"%s" "%s" "%s" "%s" 2>&1',
    $pythonPath,
    $scriptPath,
    $input_file,
    $input_type
);

error_log("Executing command: " . $command);
$output = shell_exec($command);

//debug logging


error_log("Raw output: " . (isset($output) ? $output : 'NULL'));

// Attempt to decode JSON output
$result = json_decode($output, true);

// Initialize variables
$prediction = "Error";
$score = "-";
$error_msg = null;
$json_file = null;
$csv_file = null;
$results_data = [];

if (!$result || isset($result['error'])) {
    $error_msg = isset($result['error']) ? $result['error'] : "Could not parse Python output.";
} else {
    $prediction = isset($result['status']) ? $result['status'] : "Unknown";
    $score = isset($result['count']) ? $result['count'] : "-";
    
    // Get file paths from result
    $json_file_path = isset($result['json_result']) ? $result['json_result'] : null;
    $csv_file_path = isset($result['csv_result']) ? $result['csv_result'] : null;
    
    // Convert absolute paths to web-accessible URLs
    if ($json_file_path && file_exists($json_file_path)) {
        // Get just the filename
        $json_filename = basename($json_file_path);
        $json_file = "results/" . $json_filename;
        
        // Read JSON data for display
        $json_content = file_get_contents($json_file_path);
        $results_data = json_decode($json_content, true);
    }
    
    if ($csv_file_path && file_exists($csv_file_path)) {
        $csv_filename = basename($csv_file_path);
        $csv_file = "results/" . $csv_filename;
    }
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Results - DeepGEN</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }
        
        /* Animated background particles */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            opacity: 0.1;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            background: white;
            border-radius: 50%;
            animation: float 20s infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); }
            25% { transform: translateY(-100px) translateX(50px); }
            50% { transform: translateY(-50px) translateX(-50px); }
            75% { transform: translateY(-150px) translateX(100px); }
        }
        
        header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            text-align: center;
            padding: 2em 1em;
            position: relative;
            z-index: 10;
        }
        
        header h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.3em;
            font-weight: 800;
            letter-spacing: -1px;
        }
        
        header p {
            color: #666;
            font-size: 1.1em;
            font-weight: 300;
        }
        
        .container {
            max-width: 1200px;
            margin: 3em auto;
            padding: 0 2em;
            position: relative;
            z-index: 10;
        }
        
        .result-box {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            padding: 3em;
            margin-bottom: 2em;
            border: 1px solid rgba(255,255,255,0.2);
            animation: slideUp 0.5s ease;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .status-header {
            text-align: center;
            margin-bottom: 2em;
        }
        
        .status-icon {
            font-size: 5em;
            margin-bottom: 0.3em;
            animation: bounce 1s ease;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        
        .status-icon.success { 
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .status-icon.error {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        h2 {
            color: #1e3a8a;
            font-size: 2em;
            margin-bottom: 0.5em;
            font-weight: 700;
        }
        
        h3 {
            color: #1e3a8a;
            font-size: 1.5em;
            margin: 2em 0 1em 0;
            font-weight: 700;
        }
        
        .success-message {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
            border-left: 4px solid #10b981;
            padding: 1.5em;
            border-radius: 12px;
            margin: 2em 0;
        }
        
        .error-message {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
            border-left: 4px solid #ef4444;
            padding: 1.5em;
            border-radius: 12px;
            margin: 2em 0;
            animation: shake 0.5s;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5em;
            margin: 2em 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            padding: 1.5em;
            border-radius: 16px;
            text-align: center;
            border: 2px solid rgba(102, 126, 234, 0.2);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5em;
        }
        
        .stat-value {
            color: #1e3a8a;
            font-size: 2em;
            font-weight: 800;
        }
        
        /* Results Table */
        .results-table-container {
            overflow-x: auto;
            margin: 2em 0;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .results-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        .results-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .results-table th {
            padding: 1em;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .results-table td {
            padding: 1em;
            border-bottom: 1px solid #e5e7eb;
            color: #374151;
        }
        
        .results-table tbody tr:hover {
            background: rgba(102, 126, 234, 0.05);
        }
        
        .prediction-badge {
            display: inline-block;
            padding: 0.4em 1em;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85em;
        }
        
        .badge-antigenic {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%);
            color: #059669;
            border: 1px solid #10b981;
        }
        
        .badge-non-antigenic {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
            color: #dc2626;
            border: 1px solid #ef4444;
        }
        
        .confidence-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.3em;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 1s ease;
        }
        
        .download-section {
            text-align: center;
            margin: 3em 0 2em 0;
        }
        
        .download-buttons {
            display: flex;
            gap: 1em;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .download-btn {
            display: inline-flex;
            align-items: center;
            gap: 0.7em;
            padding: 14px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            position: relative;
            overflow: hidden;
        }
        
        .download-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s;
        }
        
        .download-btn:hover::before {
            left: 100%;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        
        .download-btn .icon {
            font-size: 1.3em;
        }
        
        .action-buttons {
            text-align: center;
            margin-top: 2em;
        }
        
        button, .btn {
            display: inline-block;
            padding: 14px 30px;
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            border: 2px solid #667eea;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
        }
        
        button:hover, .btn:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }
        
        .info-box {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%);
            border-left: 4px solid #3b82f6;
            padding: 1.5em;
            border-radius: 12px;
            margin: 2em 0;
        }
        
        .info-box p {
            color: #555;
            line-height: 1.6;
            margin: 0.5em 0;
        }
        
        .info-box strong {
            color: #1e3a8a;
        }
        
        footer {
            text-align: center;
            color: rgba(255,255,255,0.9);
            padding: 2em 1em;
            font-size: 0.95em;
            position: relative;
            z-index: 10;
            background: rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            margin-top: 3em;
        }
        
        footer strong {
            color: white;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .container { padding: 0 1em; }
            .result-box { padding: 2em 1.5em; }
            h2 { font-size: 1.5em; }
            .stats-grid { grid-template-columns: 1fr; }
            .download-buttons { flex-direction: column; }
            .results-table { font-size: 0.85em; }
            .results-table th, .results-table td { padding: 0.7em; }
        }
    </style>
</head>
<body>
    <!-- Animated background -->
    <div class="bg-animation">
        <div class="particle" style="width: 3px; height: 3px; left: 10%; top: 20%; animation-delay: 0s;"></div>
        <div class="particle" style="width: 4px; height: 4px; left: 30%; top: 40%; animation-delay: 2s;"></div>
        <div class="particle" style="width: 2px; height: 2px; left: 50%; top: 10%; animation-delay: 4s;"></div>
        <div class="particle" style="width: 5px; height: 5px; left: 70%; top: 60%; animation-delay: 1s;"></div>
        <div class="particle" style="width: 3px; height: 3px; left: 90%; top: 30%; animation-delay: 3s;"></div>
        <div class="particle" style="width: 4px; height: 4px; left: 20%; top: 70%; animation-delay: 5s;"></div>
        <div class="particle" style="width: 2px; height: 2px; left: 60%; top: 80%; animation-delay: 2.5s;"></div>
        <div class="particle" style="width: 3px; height: 3px; left: 80%; top: 15%; animation-delay: 4.5s;"></div>
    </div>

    <header>
        <h1>DeepGEN</h1>
        <p>Prediction Results</p>
    </header>

    <div class="container">
        <div class="result-box">
            <div class="status-header">
                <?php if (isset($error_msg)): ?>
                    <div class="status-icon error">❌</div>
                    <h2>Prediction Error</h2>
                <?php else: ?>
                    <div class="status-icon success">✅</div>
                    <h2>Prediction Complete!</h2>
                <?php endif; ?>
            </div>

            <?php if (isset($error_msg)): ?>
                <div class="error-message">
                    <p style="color: #dc2626; font-weight: 600; font-size: 1.1em; margin-bottom: 0.5em;">
                        ⚠️ An error occurred during prediction
                    </p>
                    <p style="color: #666; margin: 0;">
                        <strong>Error Details:</strong> <?= htmlspecialchars($error_msg) ?>
                    </p>
                </div>
                
                <div class="info-box">
                    <p><strong>💡 Troubleshooting Tips:</strong></p>
                    <p>• Ensure your sequence contains at least 20 valid amino acids</p>
                    <p>• Check that your file format is correct (FASTA or PDB)</p>
                    <p>• Try submitting a different sequence</p>
                </div>
            <?php else: ?>
                <div class="success-message">
                    <p style="color: #059669; font-weight: 600; font-size: 1.1em; margin-bottom: 0.5em;">
                        🎉 Your protein sequence has been analyzed successfully!
                    </p>
                    <p style="color: #555; margin: 0;">
                        The prediction results are ready for download below.
                    </p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Status</div>
                        <div class="stat-value"><?= htmlspecialchars($prediction) ?></div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Sequences Processed</div>
                        <div class="stat-value"><?= htmlspecialchars($score) ?></div>
                    </div>
                    <?php if (!empty($results_data)): ?>
                        <?php
                            $antigenic_count = 0;
                            $non_antigenic_count = 0;
                            foreach ($results_data as $res) {
                                if (isset($res['Final_Prediction']) && $res['Final_Prediction'] === 'Antigenic') {
                                    $antigenic_count++;
                                } else {
                                    $non_antigenic_count++;
                                }
                            }
                        ?>
                        <div class="stat-card">
                            <div class="stat-label">Antigenic</div>
                            <div class="stat-value" style="color: #059669;"><?= $antigenic_count ?></div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Non-Antigenic</div>
                            <div class="stat-value" style="color: #dc2626;"><?= $non_antigenic_count ?></div>
                        </div>
                    <?php endif; ?>
                </div>

                <?php if (!empty($results_data)): ?>
                    <h3>📊 Detailed Prediction Results</h3>
                    <div class="results-table-container">
                        <table class="results-table">
                            <thead>
                                <tr>
                                    <th>Sequence ID</th>
                                    <th>Prediction</th>
                                    <th>Confidence</th>
                                    <th>ProtBERT Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($results_data as $index => $res): ?>
                                    <tr>
                                        <?= htmlspecialchars(isset($res['Sequence_ID']) ? $res['Sequence_ID'] : ("Sequence " . ($index + 1))) ?> </strong></td>
                                        <td>
                                            <?php 
                                                $pred = isset($res['Final_Prediction']) ? $res['Final_Prediction'] : 'Unknown';
                                                $badgeClass = ($pred === 'Antigenic') ? 'badge-antigenic' : 'badge-non-antigenic';
                                            ?>
                                            <span class="prediction-badge <?= $badgeClass ?>">
                                                <?= htmlspecialchars($pred) ?>
                                            </span>
                                        </td>
                                        <td>
                                            <?php 
                                                $confidence = isset($res['Confidence']) ? floatval($res['Confidence']) : 0;
                                                $confidence_percent = round($confidence * 100, 2);
                                            ?>
                                            <div><?= $confidence_percent ?>%</div>
                                            <div class="confidence-bar">
                                                <div class="confidence-fill" style="width: <?= $confidence_percent ?>%"></div>
                                            </div>
                                        </td>
                                        <td><?= isset($res['ProtBERT_Score']) ? number_format($res['ProtBERT_Score'], 4) : 'N/A' ?></td>
                                    </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                <?php endif; ?>

                <div class="download-section">
                    <h3>📥 Download Results</h3>
                    <div class="download-buttons">
                        <?php if ($json_file): ?>
                            <a class="download-btn" href="<?= htmlspecialchars($json_file) ?>" download>
                                <span class="icon">📄</span>
                                <span>Download JSON</span>
                            </a>
                        <?php endif; ?>
                        <?php if ($csv_file): ?>
                            <a class="download-btn" href="<?= htmlspecialchars($csv_file) ?>" download>
                                <span class="icon">📊</span>
                                <span>Download CSV</span>
                            </a>
                        <?php endif; ?>
                    </div>
                </div>

                <div class="info-box">
                    <p><strong>📌 Results Include:</strong></p>
                    <p>• ProtBERT probability scores for antigenicity prediction</p>
                    <p>• Physicochemical feature predictions and analysis</p>
                    <p>• Consensus classification (Antigenic/Non-antigenic)</p>
                    <p>• Confidence scores for each prediction</p>
                </div>
            <?php endif; ?>

            <div class="action-buttons">
                <form action="index1.html" method="get" style="display: inline;">
                    <button type="submit">🔄 Predict Another Sequence</button>
                </form>
            </div>
        </div>
    </div>

    <footer>
        © 2025 <strong>DeepGEN</strong> | Advanced Protein Antigenicity Prediction
    </footer>
</body>
</html>