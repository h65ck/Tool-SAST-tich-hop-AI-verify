<?php
require_once __DIR__ . '/../config/db.php';

function sanitizeProductId($id) {
    // [SANITIZER]
    return addslashes($id);
}

function handleImageUpload($file, $current_image = '') {
    $upload_dir = __DIR__ . '/../uploads/products/';
    if (!is_dir($upload_dir)) {
        mkdir($upload_dir, 0777, true);
    }
    
    if (isset($file) && $file['error'] == 0) {
        $file_extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        $allowed_exts = ['jpg', 'jpeg', 'png', 'gif'];
        
        if (in_array($file_extension, $allowed_exts)) {
            $new_filename = uniqid('prod_') . '.' . $file_extension;
            $target_path = $upload_dir . $new_filename;
            
            if (move_uploaded_file($file['tmp_name'], $target_path)) {
                return '/uploads/products/' . $new_filename;
            }
        }
    }
    return $current_image;
}

function addProduct($name, $description, $price, $owner_id, $image_path = '') {
    global $conn;
    $sql = "INSERT INTO products (name, description, price, owner_id, image) VALUES ('$name', '$description', '$price', '$owner_id', '$image_path')";
    return mysqli_query($conn, $sql);
}

function editProduct($id, $name, $description, $price, $image_path) {
    global $conn;
    $clean_id = sanitizeProductId($id);
    $sql = "UPDATE products SET name='$name', description='$description', price='$price', image='$image_path' WHERE id = {$clean_id}";
    return mysqli_query($conn, $sql);
}

function deleteProduct($id) {
    global $conn;
    // [SINK]
    $sql = "DELETE FROM products WHERE id = {$id}";
    return mysqli_query($conn, $sql);
}
?>
