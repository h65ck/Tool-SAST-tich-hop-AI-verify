<?php
require_once '../config/db.php';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'];
    $password = $_POST['password'];
    $role = 'user';

    $sql = "INSERT INTO users (username, password, role) VALUES ('$username', '$password', '$role')";
    
    if (mysqli_query($conn, $sql)) {
        header("Location: login.php");
        exit();
    } else {
        $error = "Lỗi: " . mysqli_error($conn);
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Register - VulnMarket</title>
</head>
<body>
    <h2>Register</h2>
    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
    <form method="POST" action="">
        <label>Username:</label><br>
        <input type="text" name="username"><br><br>
        <label>Password:</label><br>
        <input type="password" name="password"><br><br>
        <button type="submit">Register</button>
    </form>
    <br>
    <a href="login.php">Login</a> | <a href="../index.php">Trang chủ</a>
</body>
</html>
