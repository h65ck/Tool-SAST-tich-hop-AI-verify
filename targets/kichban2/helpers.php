<?php
function buildQuery($id) {
    return "SELECT * FROM users WHERE id = " . $id;
}
?>
