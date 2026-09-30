<?php
require_once '../includes/auth.php';
require_once '../includes/product_helper.php';

requireRole("seller");

if (isset($_GET['id'])) {
    // [SOURCE]
    $raw_id = $_GET['id'];
    
    $clean_id = sanitizeProductId($raw_id);
    
    if (deleteProduct($clean_id)) {
        header("Location: dashboard.php?msg=deleted");
        exit();
    } else {
        echo "Lỗi xóa sản phẩm: " . mysqli_error($conn);
    }
} else {
    header("Location: dashboard.php");
    exit();
}
?>
