<?php
require_once '../config/db.php';
require_once '../includes/auth.php';

if (isLoggedIn()) {
    header("Location: ../index.php");
    exit();
}

$error = '';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'];
    $password = $_POST['password'];

    $sql = "SELECT * FROM users WHERE username='$username' AND password='$password'";
    $result = mysqli_query($conn, $sql);

    if ($result && mysqli_num_rows($result) > 0) {
        $user = mysqli_fetch_assoc($result);
        
        $_SESSION['user'] = [
            'id' => $user['id'],
            'username' => $user['username'],
            'role' => $user['role']
        ];

        if ($user['role'] == 'admin') {
            header("Location: ../admin/index.php");
        } else if ($user['role'] == 'seller') {
            header("Location: ../seller/dashboard.php");
        } else {
            header("Location: ../index.php");
        }
        exit();
    } else {
        $error = "Sai username hoặc password!";
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Login - VulnMarket</title>
</head>
<body>
    <h2>Login</h2>
    <?php if ($error) echo "<p style='color:red;'>$error</p>"; ?>
    <form method="POST" action="">
        <label>Username:</label><br>
        <input type="text" name="username"><br><br>
        <label>Password:</label><br>
        <input type="password" name="password"><br><br>
        <button type="submit">Login</button>
    </form>
    <br>
    <a href="register.php">Register</a> | <a href="../index.php">Trang chủ</a>
</body>
</html>
