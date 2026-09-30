<?php
require_once 'config/db.php';
require_once 'includes/helpers.php';
require_once 'includes/auth.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VulnMarket</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .product { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; }
        .product img { max-width: 200px; }
        .nav { margin-bottom: 20px; padding: 10px; background: #eee; }
    </style>
</head>
<body>

    <div class="nav">
        <?php if (isLoggedIn()): ?>
            Welcome <?php echo $_SESSION['user']['username']; ?> | 
            Role: <?php echo getRole(); ?> | 
            <a href="auth/logout.php">Logout</a>
            <?php if (getRole() == 'admin'): ?>
                 | <a href="admin/index.php">Admin Dashboard</a>
            <?php elseif (getRole() == 'seller'): ?>
                 | <a href="seller/dashboard.php">Seller Dashboard</a>
            <?php endif; ?>
        <?php else: ?>
            <a href="auth/login.php">Login</a> | 
            <a href="auth/register.php">Register</a>
        <?php endif; ?>
    </div>

    <h1>VulnMarket</h1>
    
    <?php
    $sql = "SELECT * FROM products";
    $result = mysqli_query($conn, $sql);
    
    if ($result && mysqli_num_rows($result) > 0) {
        while ($row = mysqli_fetch_assoc($result)) {
            echo '<div class="product">';
            echo '<h3>' . $row['name'] . '</h3>';
            if (!empty($row['image'])) {
                echo '<img src="' . $row['image'] . '" alt="Product Image"><br>';
            }
            $price = isset($row['price']) ? formatPrice($row['price']) : 0;
            echo '<p class="price">Price: $' . $price . '</p>';
            echo '<p>' . $row['description'] . '</p>';
            echo '</div>';
        }
    } else {
        echo '<p>No products found</p>';
    }
    
    mysqli_close($conn);
    ?>

</body>
</html>