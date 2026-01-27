arr = list('hello world')[::-1]


def func(x, arr_2):
    if x == len(arr_2):
        return
    x_1 = len(arr_2) - 1 - x
    print(arr_2[x_1], end='')
    func(x + 1, arr_2)


a = lambda x: func(x, arr)
a(0)

