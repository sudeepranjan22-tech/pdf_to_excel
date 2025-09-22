<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "Starting upload process...<br>";

// Get the base directory one level above backend
$baseDir = dirname(__DIR__);

$uploadDir = $baseDir . '/uploads/';
$outputDir = $baseDir . '/outputs/';

// Create folders if they don't exist
if (!file_exists($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}
if (!file_exists($outputDir)) {
    mkdir($outputDir, 0777, true);
}

// Only proceed if POST and file uploaded
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_FILES['pdf_file']) || $_FILES['pdf_file']['error'] !== UPLOAD_ERR_OK) {
        die("❌ Upload failed or no file uploaded.");
    }

    $uploadedFile = $_FILES['pdf_file'];
    $originalName = basename($uploadedFile['name']);

    // Validate MIME type strictly (sometimes mime_content_type can be unreliable)
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $fileType = finfo_file($finfo, $uploadedFile['tmp_name']);
    finfo_close($finfo);

    if ($fileType !== 'application/pdf') {
        die("❌ Only PDF files are allowed.");
    }

    $uploadPath = $uploadDir . $originalName;

    if (!move_uploaded_file($uploadedFile['tmp_name'], $uploadPath)) {
        die("❌ Failed to move uploaded file.");
    }

    echo "✅ File uploaded successfully to: $uploadPath <br>";

    // Prepare and run Python command
    $safePdfPath = escapeshellarg($uploadPath);

    // IMPORTANT: Use full path to python and script if needed
    // Adjust 'python' to 'python3' or full path if necessary
    $pythonPath = 'python'; // or '/usr/bin/python3' or 'C:\\Python39\\python.exe'
    $scriptPath = escapeshellarg($baseDir . '/backend/pdf_to_excel.py');

    $command = "$pythonPath $scriptPath $safePdfPath 2>&1";

    echo "Executing command:<br><code>$command</code><br>";

    $output = shell_exec($command);

    if ($output === null) {
        echo "❌ Failed to execute Python script.";
    } else {
        echo "<pre>Python output:\n$output</pre>";
    }

    // Optionally, show the output Excel file path (if your python script creates it)
    // For example:
    $excelFile = $outputDir . "bank_statement.xlsx"; // adjust as per your python naming
    if (file_exists($excelFile)) {
        echo "✅ Excel file created at: $excelFile<br>";
        echo "<a href='" . str_replace($baseDir, '', $excelFile) . "' download>Download Excel</a>";
    } else {
        #echo "⚠️ Excel file not found. Check Python script.";
        ;
    }
} else {
    echo "Please upload a PDF file via POST.";
}
#remove below lines to debug php file as the project runs
header("Location: /pdf_to_excel/frontend/frontend.html?status=success");
exit();