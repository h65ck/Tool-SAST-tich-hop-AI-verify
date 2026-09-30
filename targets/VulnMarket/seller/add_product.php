<?php
require_once '../includes/auth.php';
require_once '../includes/product_helper.php';

requireRole("seller");

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name = $_POST['name'];
    $description = $_POST['description'];
    $price = $_POST['price'];
    $owner_id = $_SESSION['user']['id'];
    
    $image_path = '';
    if (isset($_FILES['image']) && $_FILES['image']['error'] == 0) {
        $image_path = handleImageUpload($_FILES['image']);
    }
    
    if (addProduct($name, $description, $price, $owner_id, $image_path)) {
        header("Location: dashboard.php?msg=added");
        exit();
    } else {
        global $conn;
        $error = "Lỗi thêm sản phẩm: " . mysqli_error($conn);
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Add Product - Seller</title>
</head>
<body>
    <h1>Add Product</h1>
    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
    <form method="POST" action="" enctype="multipart/form-data">
        <label>Name:</label><br>
        <input type="text" name="name" required><br><br>
        
        <label>Description:</label><br>
        <textarea name="description" required></textarea><br><br>
        
        <label>Price:</label><br>
        <input type="number" name="price" required><br><br>
        
        <label>Product Image:</label><br>
        <input type="file" name="image" accept="image/*"><br><br>
        
        <button type="submit">Add</button>
    </form>
    <br>
    <a href="dashboard.php">Back to Dashboard</a>
</body>
</html>
