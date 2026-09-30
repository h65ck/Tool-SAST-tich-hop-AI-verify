<?php
if (isset($_POST['Submit'])) {
    $target = $_REQUEST['ip'];

    $substitutions = array(
        '&&' => '',
        ';'  => '',
    );

    $target = str_replace(array_keys($substitutions), $substitutions, $target);

    $cmd = shell_exec('ping -c 4 ' . $target);
}
?>
