# 有问题的代码示例 - 包含多种代码坏味道和潜在Bug
# 用于演示Code Review Agent的审查能力

import os
import sys

# 全局变量 - 不推荐
global_count = 0
global_data = {}

def process_data(data, flag, option, mode, extra, debug):
    # 函数过长，参数过多，缺少类型注解
    result = []
    for i in range(len(data)):
        if flag == True:
            if option == 1:
                if mode == "fast":
                    # 深层嵌套
                    if extra != None:
                        try:
                            x = data[i]
                            y = x * 2
                            if debug:
                                print("processing", i)
                            result.append(y)
                        except:
                            # bare except
                            pass
                    else:
                        if debug:
                            print("extra is None")
                        result.append(data[i])
                else:
                    if i % 2 == 0:
                        result.append(data[i] * 3)
                    else:
                        result.append(data[i])
            else:
                result.append(data[i] * flag)
        else:
            result.append(0)

    global global_count
    global_count += len(result)
    return result

class Manager:
    def __init__(self):
        self.data = []
        self.cache = None

    def do_everything(self, input_data, operation, params, config, settings, env):
        # 上帝方法 - 做了太多事情
        if operation == "add":
            for item in input_data:
                self.data.append(item)
        elif operation == "remove":
            for item in input_data:
                if item in self.data:
                    self.data.remove(item)
        elif operation == "sort":
            self.data.sort()
        elif operation == "search":
            results = []
            for item in self.data:
                if params in str(item):
                    results.append(item)
            return results
        elif operation == "clear":
            self.data = []
        elif operation == "stats":
            return {
                "count": len(self.data),
                "first": self.data[0] if self.data else None,
                "last": self.data[-1] if self.data else None,
            }

    def unsafe_operation(self):
        # 可能的除零错误
        count = len(self.data)
        average = sum(self.data) / count
        return average

    def get_item(self, index):
        # 没有边界检查
        return self.data[index]

def main():
    mgr = Manager()
    data = [1, 2, 3, 4, 5]

    mgr.do_everything(data, "add", None, None, None, None)
    print(mgr.do_everything(None, "stats", None, None, None, None))

    result = process_data(data, True, 1, "fast", "extra", True)
    print("Result:", result)

    # 不安全的操作
    mgr.data = []
    try:
        avg = mgr.unsafe_operation()
        print("Average:", avg)
    except:
        pass

if __name__ == "__main__":
    main()
