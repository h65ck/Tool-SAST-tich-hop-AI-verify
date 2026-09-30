# [CROSS_FILE_CHANGE]
import os #thu vien de lam viec voi duong dan va tap tin

class ProjectScanner:
    def collect_php_files(self, target_path):
        # [CROSS_FILE_CHANGE]
        if not os.path.exists(target_path):#neu k ton tai duong dan thi tra ve 1 list rong
            return []

        if os.path.isfile(target_path):
            if target_path.endswith(".php"):
                return [os.path.normpath(target_path)]#normpath de chuan hoa duong dan
            return []

        php_files = []
        ignored_dirs = {"vendor", "node_modules", ".git", "__pycache__"}

        for root, dirs, files in os.walk(target_path):#duyet qua cac thu muc va tap tin trong duong dan target_path 
            # Modifying dirs in-place to prune them from recursion
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for file in files:
                if file.endswith(".php"):
                    php_files.append(os.path.normpath(os.path.join(root, file)))

        return php_files
