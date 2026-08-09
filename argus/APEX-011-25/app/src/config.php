<?php
/**
 * Database Configuration
 */

define('DB_HOST', getenv('MYSQL_HOST') ?: 'localhost');
define('DB_PORT', getenv('MYSQL_PORT') ?: '3306');
define('DB_NAME', getenv('MYSQL_DATABASE') ?: 'vulnerable_app');
define('DB_USER', getenv('MYSQL_USER') ?: 'app');
define('DB_PASS', getenv('MYSQL_PASSWORD') ?: 'app_password_secure');

// Database connection
function getDbConnection() {
    static $pdo = null;

    if ($pdo === null) {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
            $pdo = new PDO($dsn, DB_USER, DB_PASS, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false
            ]);
        } catch (PDOException $e) {
            die("Database connection failed: " . $e->getMessage());
        }

        ensureFlagExists($pdo);
    }

    return $pdo;
}

function ensureFlagExists($pdo) {
    static $checked = false;
    if ($checked) return;
    $checked = true;

    $flag = getenv('FLAG');
    if (!$flag) return;

    try {
        $stmt = $pdo->prepare("SELECT id FROM secrets WHERE description = 'CTF flag for second-order SQLi challenge'");
        $stmt->execute();
        $existing = $stmt->fetch();

        if (!$existing) {
            $stmt = $pdo->prepare("INSERT INTO secrets (flag, description) VALUES (?, 'CTF flag for second-order SQLi challenge')");
            $stmt->execute([$flag]);
        } else {
            $stmt = $pdo->prepare("UPDATE secrets SET flag = ? WHERE description = 'CTF flag for second-order SQLi challenge'");
            $stmt->execute([$flag]);
        }
    } catch (PDOException $e) {
        // Silently ignore - table might not exist yet
    }
}

// Start session
session_start();
