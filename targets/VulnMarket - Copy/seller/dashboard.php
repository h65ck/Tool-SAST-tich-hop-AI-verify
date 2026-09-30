<?php
require_once '../includes/auth.php';
require_once '../config/db.php';

requireRole("seller");

$owner_id = $_SESSION['user']['id'];
$sql = "SELECT * FROM products WHERE owner_id = '$owner_id'";
$result = mysqli_query($conn, $sql);
?>
<!DOCTYPE html>
<html>
<head>
    <title>Seller Dashboard</title>
    <style>
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
    </style>
</head>
<body>
    <h1>Seller Dashboard</h1>
    <p>Welcome, <?php echo $_SESSION['user']['username']; ?>!</p>
    <a href="../index.php">Trang chủ</a> | <a href="../auth/logout.php">Logout</a>
    <br><br>
    <a href="add_product.php"><button>Add Product</button></a>
    <br><br>
    
    <?php if (isset($_GET['msg']) && $_GET['msg'] == 'deleted') echo "<p style='color:green;'>Sản phẩm đã bị xóa!</p>"; ?>
    <?php if (isset($_GET['msg']) && $_GET['msg'] == 'added') echo "<p style='color:green;'>Thêm sản phẩm thành công!</p>"; ?>

    <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Price</th>
            <th>Description</th>
            <th>Action</th>
        </tr>
        <?php
        if ($result && mysqli_num_rows($result) > 0) {
            while ($row = mysqli_fetch_assoc($result)) {
                echo "<tr>";
                echo "<td>" . $row['id'] . "</td>";
                echo "<td>" . $row['name'] . "</td>";
                echo "<td>$" . $row['price'] . "</td>";
                echo "<td>" . $row['description'] . "</td>";
                echo "<td><a href='delete_product.php?id=" . $row['id'] . "'><button>Delete</button></a></td>";
                echo "</tr>";
            }
        } else {
            echo "<tr><td colspan='5'>Chưa có sản phẩm nào.</td></tr>";
        }
        ?>
    </table>
</body>
</html>
