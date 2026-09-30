<?php

function sanitizeInput($input) {
    return trim($input);
}

function safeUsername($username) {
    return preg_match('/^[a-zA-Z0-9]+$/', $username);
}

function formatPrice($price) {
    return number_format($price);
}

?>
