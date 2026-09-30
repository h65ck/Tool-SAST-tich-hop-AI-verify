<?php
require_once __DIR__ . '/../config/db.php';

function sanitizeProductId($id) {
    // [SANITIZER]
    return addslashes($id);
}

function addProduct($name, $description, $price, $owner_id) {
    global $conn;
    $sql = "INSERT INTO products (name, description, price, owner_id) VALUES ('$name', '$description', '$price', '$owner_id')";
    return mysqli_query($conn, $sql);
}

function deleteProduct($id) {
    global $conn;
    // [SINK]
    $sql = "DELETE FROM products WHERE id = {$id}";
    return mysqli_query($conn, $sql);
}
?>
