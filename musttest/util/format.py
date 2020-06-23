

def print_formatter(inner_func):
    def wrapper_func(formatting, *args, **kwargs):
        tmp_str = "="*102
        func_name = inner_func.__name__
        tmp_str = tmp_str[:len(tmp_str)-len(func_name)//2-1]
        tmp_str = f'{tmp_str} {func_name} {tmp_str}'
        print(tmp_str)
        for item in formatting:
            print(item)
        inner_func(*args, **kwargs)
    return wrapper_func


def unittest_formatter(test_file_path: str, root_path: str):
    test_file_rel_path = test_file_path.replace(root_path,'')
    module_name = ""
    with open(test_file_path, 'r',  encoding="UTF8") as test:
        line = test.readline()
        while line:
            if line.strip() and line.strip()[0] != "#" and 'class' in line.lower():
                module_name = line.split("(")[0].split("class ")[-1]
                break
            line = test.readline()
    test_file_rel_path = test_file_rel_path.split(".py")[0] + "/" + module_name
    res = test_file_rel_path.replace("/", ".")
    if res[0] == ".":
        res = res[1:]
    return res
