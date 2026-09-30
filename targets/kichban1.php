<?php
// simple_sqli_filter_test.php

$id = $_GET['id'] ?? '1';
$mode = $_GET['mode'] ?? 'vuln';

$conn = null;
$query = "SELECT first_name, last_name FROM users WHERE user_id = 1";

if ($mode === "vuln") {
    $query = "SELECT first_name, last_name FROM users WHERE user_id = '$id';";
} elseif ($mode === "safe_overwrite") {
    $id = 1; // SAFE overwrite
    $query = "SELECT first_name, last_name FROM users WHERE user_id = '$id';";
}

mysqli_query($conn, $query); // SINK: SQL injection

?>