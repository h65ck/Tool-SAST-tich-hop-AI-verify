<?php
require_once '../includes/auth.php';
requireRole("admin");
?>
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
</head>
<body>
    <h1>Admin Dashboard</h1>
    <p>Welcome, <?php echo $_SESSION['user']['username']; ?>!</p>
    <a href="../index.php">Trang chủ</a> | <a href="../auth/logout.php">Logout</a>
</body>
</html>
