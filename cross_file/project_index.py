# [CROSS_FILE_CHANGE]
class ProjectIndex:
    def __init__(self):
        # [CROSS_FILE_CHANGE]
        self.files = {}#luu tru thong tin ve cac file php, voi key la duong dan file va value la mot dict chua source_bytes, tree, semgrep_data
        self.functions = {}#luu tru thong tin ve cac ham, voi key la ten ham va value la mot dict chua thong tin ve ham do (nhu file_path, parameters, return_type, etc.)
        self.function_summaries = {}#luu tru tom tat ve cac ham, voi key la ten ham va value la mot chuoi tom tat ve ham do
        self.includes = {}#luu tru thong tin ve cac include/require, voi key la duong dan file va value la mot list chua cac duong dan file duoc include/require
        self.duplicate_functions = {}#luu tru thong tin ve cac ham bi trung ten, voi key la ten ham va value la mot list chua cac dict thong tin ve ham do (nhu file_path, parameters, return_type, etc.)

    def add_file(self, file_path, source_bytes, tree, semgrep_data):
        self.files[file_path] = {
            "source_bytes": source_bytes,#noi dung file
            "tree": tree,#ast cua file
            "semgrep_data": semgrep_data#ket qua semgrep khi chay tren file do, co the chua thong tin ve cac ham, include, etc. trong file do
        }

    def add_functions(self, file_path, functions):
        for func_name, func_info in functions.items():
            # Clone or modify the dict to include the file_path reference
            func_info = dict(func_info)#tao mot ban sao cua func_info de them thong tin file_path ma khong thay doi dict goc trong functions
            func_info["file_path"] = file_path#them thong tin file_path vao func_info de biet ham do duoc dinh nghia trong file nao

            if func_name in self.functions:
                print(f"[WARN] Duplicate function name: {func_name} in {file_path}. Keeping first definition.")
                self.duplicate_functions.setdefault(func_name, []).append({
                    "file_path": file_path,
                    "func_info": func_info
                })
                continue

            self.functions[func_name] = func_info

    def add_function_summary(self, func_name, summary):
        self.function_summaries[func_name] = summary

    def get_function_summary(self, func_name):
        return self.function_summaries.get(func_name)

    def get_all_function_summaries(self):
        return self.function_summaries

    def add_includes(self, file_path, includes):
        self.includes[file_path] = includes
