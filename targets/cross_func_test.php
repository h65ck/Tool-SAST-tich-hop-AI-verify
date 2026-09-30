<?php

function buildQuery($id) {
    return "SELECT * FROM users WHERE id = " . $id;
}

function runQuery($conn, $sql) {
    mysqli_query($conn, $sql);
}

$id = $_GET['id'] ?? '1';
$conn = null;

if ($_GET['test1']) {
    $query = buildQuery($id);
    mysqli_query($conn, $query);
} else {
    $query2 = "SELECT * FROM users WHERE id = " . $id;
    runQuery($conn, $query2);
}

?>
