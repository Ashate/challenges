<?php
$pageTitle = 'Profile - VulnApp';
require_once 'includes/header.php';
requireLogin();

$user = getCurrentUser();
$pdo = getDbConnection();

// VULNERABILITY: Second-order SQL injection trigger
//
// The developer retrieves the username from the session/database
// and trusts it because "it came from our system".
// But the username was user-controlled at registration time!
//
// If username = "' UNION SELECT flag,2,3,4,5,6,7 FROM secrets-- "
// Then the query becomes:
//   SELECT * FROM activity_logs
//   WHERE username = '' UNION SELECT flag,2,3,4,5,6,7 FROM secrets-- '

$username = $user['username'];  // "Trusted" data from database

// VULNERABLE QUERY - username used directly without parameterization
$query = "SELECT * FROM activity_logs WHERE username = '$username' ORDER BY created_at DESC LIMIT 50";
$queryDebug = $query;

$logs = [];
$error = '';

try {
    $result = $pdo->query($query);
    $logs = $result->fetchAll();
} catch (PDOException $e) {
    $error = "Query error: " . $e->getMessage();
}
?>

<div class="card">
    <h2>My Profile</h2>

    <table>
        <tr>
            <th>Username</th>
            <td><?= htmlspecialchars($user['username']) ?></td>
        </tr>
        <tr>
            <th>Email</th>
            <td><?= htmlspecialchars($user['email']) ?></td>
        </tr>
        <tr>
            <th>Role</th>
            <td><?= htmlspecialchars($user['role']) ?></td>
        </tr>
    </table>
</div>

<div class="card">
    <h3>My Activity Logs</h3>

    <?php if ($error): ?>
        <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <?php if ($queryDebug): ?>
        <div class="debug-info">
            <strong>Debug - SQL Query:</strong><br>
            <code><?= htmlspecialchars($queryDebug) ?></code>
        </div>
    <?php endif; ?>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>User ID</th>
                <th>Username</th>
                <th>Action</th>
                <th>Details</th>
                <th>IP Address</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody>
            <?php if (empty($logs)): ?>
                <tr>
                    <td colspan="7" style="text-align: center;">No activity found</td>
                </tr>
            <?php else: ?>
                <?php foreach ($logs as $log): ?>
                <tr>
                    <td><?= htmlspecialchars($log['id'] ?? '') ?></td>
                    <td><?= htmlspecialchars($log['user_id'] ?? '') ?></td>
                    <td><?= htmlspecialchars($log['username'] ?? '') ?></td>
                    <td><?= htmlspecialchars($log['action'] ?? '') ?></td>
                    <td><?= htmlspecialchars($log['details'] ?? '') ?></td>
                    <td><?= htmlspecialchars($log['ip_address'] ?? '') ?></td>
                    <td><?= htmlspecialchars($log['created_at'] ?? '') ?></td>
                </tr>
                <?php endforeach; ?>
            <?php endif; ?>
        </tbody>
    </table>
</div>

<?php require_once 'includes/footer.php'; ?>
