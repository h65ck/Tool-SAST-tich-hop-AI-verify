<?php
session_start();

function isLoggedIn() {
    return isset($_SESSION['user']);
}

function getRole() {
    if (isset($_SESSION['user']['role'])) {
        return $_SESSION['user']['role'];
    }
    return null;
}

function requireLogin() {
    if (!isLoggedIn()) {
        header("Location: /auth/login.php");
        exit();
    }
}

function requireRole($role) {
    requireLogin();
    if (getRole() !== $role) {
        die("Access Denied: You do not have permission to access this page.");
    }
}
?>
