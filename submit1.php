<?php
session_start();

// === Helper: Extract sequence from FASTA text ===
function extract_sequence($text) {
    $lines = explode("\n", $text);
    $seq = "";
    foreach ($lines as $line) {
        if (strpos($line, '>') === 0) continue;
        $seq .= trim($line);
    }
    return strtoupper($seq);
}

// === Helper: Show styled error page ===
function show_error($message, $icon = "⚠️") {
    die("
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>Validation Error - DeepGEN</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2em;
            }
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
            .error-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 3em;
                border-radius: 24px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 500px;
                position: relative;
                z-index: 10;
                animation: slideUp 0.5s ease, shake 0.5s ease;
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
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-10px); }
                75% { transform: translateX(10px); }
            }
            .error-icon {
                font-size: 4em;
                margin-bottom: 0.5em;
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            h2 {
                color: #dc2626;
                margin-bottom: 0.5em;
                font-size: 1.8em;
                font-weight: 700;
            }
            .error-message {
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
                border-left: 4px solid #ef4444;
                padding: 1.5em;
                border-radius: 12px;
                margin: 1.5em 0;
                text-align: left;
            }
            .error-message p {
                color: #555;
                line-height: 1.6;
                margin: 0.5em 0;
            }
            .error-message strong {
                color: #dc2626;
            }
            a {
                display: inline-block;
                padding: 14px 30px;
                margin-top: 1em;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            a:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
            }
        </style>
    </head>
    <body>
        <div class='bg-animation'>
            <div class='particle' style='width: 3px; height: 3px; left: 10%; top: 20%; animation-delay: 0s;'></div>
            <div class='particle' style='width: 4px; height: 4px; left: 30%; top: 40%; animation-delay: 2s;'></div>
            <div class='particle' style='width: 2px; height: 2px; left: 50%; top: 10%; animation-delay: 4s;'></div>
            <div class='particle' style='width: 5px; height: 5px; left: 70%; top: 60%; animation-delay: 1s;'></div>
            <div class='particle' style='width: 3px; height: 3px; left: 90%; top: 30%; animation-delay: 3s;'></div>
        </div>
        <div class='error-container'>
            <div class='error-icon'>{$icon}</div>
            <h2>Validation Error</h2>
            <div class='error-message'>
                <p><strong>Error:</strong> {$message}</p>
            </div>
            <a href='index.html'>🏠 Return to Home</a>
        </div>
    </body>
    </html>
    ");
}

// ==========================================================
//                  1. Process Input
// ==========================================================

$inputType = "";
$finalFilePath = "";
$cleanSeq = "";

// --- CASE 1: Text sequence input ---
if (isset($_POST['sequence']) && !empty(trim($_POST['sequence']))) {
    $raw = trim($_POST['sequence']);
    $cleanSeq = extract_sequence($raw);
    
    // Validate length
    if (strlen($cleanSeq) < 20) {
        show_error(
            "Sequence must be at least 20 amino acids long. You provided " . strlen($cleanSeq) . " amino acids.",
            "📏"
        );
    }
    
    // Validate amino acids
    if (!preg_match('/^[ACDEFGHIKLMNPQRSTVWY]+$/i', $cleanSeq)) {
        show_error(
            "Invalid sequence! Only standard amino acids are allowed (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y).",
            "🧬"
        );
    }
    
    // Save sequence to a temporary fasta file
    $uploadDir = "uploads/";
    if (!is_dir($uploadDir)) mkdir($uploadDir, 0777, true);
    
    $finalFilePath = $uploadDir . "input_" . time() . ".fasta";
    file_put_contents($finalFilePath, ">input\n" . $cleanSeq);
    
    $inputType = "fasta";
}

// --- CASE 2: File upload ---
elseif (isset($_FILES['file']) && $_FILES['file']['error'] == 0) {
    
    $allowedExtensions = ['fasta', 'fa', 'pdb'];
    $fileTmp = $_FILES['file']['tmp_name'];
    $filename = $_FILES['file']['name'];
    $ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    
    if (!in_array($ext, $allowedExtensions)) {
        show_error(
            "Invalid file type! Please upload a file with one of these extensions: .fasta, .fa, or .pdb",
            "📁"
        );
    }
    
    $uploadDir = "uploads/";
    if (!is_dir($uploadDir)) mkdir($uploadDir, 0777, true);
    
    // Save file with timestamp
    $finalFilePath = $uploadDir . "upload_" . time() . "." . $ext;
    
    if (!move_uploaded_file($fileTmp, $finalFilePath)) {
        show_error(
            "File upload failed. Please check file permissions and try again.",
            "❌"
        );
    }
    
    // For FASTA – validate sequence
    if ($ext === "fasta" || $ext === "fa") {
        $text = file_get_contents($finalFilePath);
        $cleanSeq = extract_sequence($text);
        
        if (strlen($cleanSeq) < 20) {
            show_error(
                "Sequence in uploaded file must be at least 20 amino acids long. Found " . strlen($cleanSeq) . " amino acids.",
                "📏"
            );
        }
        
        if (!preg_match('/^[ACDEFGHIKLMNPQRSTVWY]+$/i', $cleanSeq)) {
            show_error(
                "Invalid residues in FASTA file! Only standard amino acids are allowed.",
                "🧬"
            );
        }
        
        $inputType = "fasta";
    }
    
    // For PDB – do NOT validate as sequence
    elseif ($ext === "pdb") {
        $inputType = "pdb";
    }
}

else {
    show_error(
        "No input provided. Please enter a sequence in the text box or upload a file.",
        "⚠️"
    );
}

// ==========================================================
//            3. Save to session & redirect to result
// ==========================================================

$_SESSION['input_path'] = $finalFilePath;
$_SESSION['input_type'] = $inputType;

header("Location: result1.php");
exit;
?>