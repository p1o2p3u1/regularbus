# here are some comments
# blablabla
"""
comments
"""
class Fibonacci:
    """
    calculate fibonacci number
    """
    def __init__(self):
        pass

    def calc(self, n):
        if n <= 0:
            return 0
        a = 0
        b = 1
        for i in range(n-1):
            c = a + b
            a = b
            b = c
        return b
