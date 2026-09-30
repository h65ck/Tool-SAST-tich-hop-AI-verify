<?php
require_once '../includes/auth.php';
require_once '../includes/product_helper.php';
require_once '../config/db.php';

requireRole("seller");

if (!isset($_GET['id'])) {
    header("Location: dashboard.php");
    exit();
}

$id = sanitizeProductId($_GET['id']);
$owner_id = $_SESSION['user']['id'];

// Lấy thông tin sản phẩm hiện tại
$sql = "SELECT * FROM products WHERE id = {$id} AND owner_id = '$owner_id'";
$result = mysqli_query($conn, $sql);
if (!$result || mysqli_num_rows($result) == 0) {
    die("Product not found or access denied.");
}
$product = mysqli_fetch_assoc($result);

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name = $_POST['name'];
    $description = $_POST['description'];
    $price = $_POST['price'];
    
    // Upload ảnh mới hoặc giữ nguyên ảnh cũ
    $image_path = $product['image'];
    if (isset($_FILES['image']) && $_FILES['image']['error'] == 0) {
        $image_path = handleImageUpload($_FILES['image'], $product['image']);
    }
    
    if (editProduct($id, $name, $description, $price, $image_path)) {
        header("Location: dashboard.php?msg=edited");
        exit();
    } else {
        $error = "Lỗi sửa sản phẩm: " . mysqli_error($conn);
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Edit Product - Seller</title>
</head>
<body>
    <h1>Edit Product</h1>
    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
    <form method="POST" action="" enctype="multipart/form-data">
        <label>Name:</label><br>
        <input type="text" name="name" value="<?php echo htmlspecialchars($product['name']); ?>" required><br><br>
        
        <label>Description:</label><br>
        <textarea name="description" required><?php echo htmlspecialchars($product['description']); ?></textarea><br><br>
        
        <label>Price:</label><br>
        <input type="number" name="price" value="<?php echo htmlspecialchars($product['price']); ?>" required><br><br>
        
        <label>Current Image:</label><br>
        <?php if (!empty($product['image'])): ?>
            <img src="<?php echo htmlspecialchars($product['image']); ?>" width="100"><br>
        <?php else: ?>
            <p>No image</p>
        <?php endif; ?>
        <br>
        
        <label>Upload New Image (optional):</label><br>
        <input type="file" name="image" accept="image/*"><br><br>
        
        <button type="submit">Save Changes</button>
    </form>
    <br>
    <a href="dashboard.php">Back to Dashboard</a>
</body>
</html>
