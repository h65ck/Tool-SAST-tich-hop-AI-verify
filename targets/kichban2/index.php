<?php
require_once "helpers.php";
require_once "db.php";

$id = $_GET['id'] ?? '1';
$conn = null;

$query = buildQuery($id);
mysqli_query($conn, $query);

$query2 = "SELECT * FROM users WHERE id = " . $id;
runQuery($conn, $query2);
?>
