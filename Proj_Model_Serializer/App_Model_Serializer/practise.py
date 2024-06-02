class A:
    def __init__(self, *args, **kwargs):
        print('A')
        pass


class B:
    def __init__(self, *args, **kwargs):
        print('B', self)


class C(A, B):
    def __init__(self, *args, **kwargs):
        A.__init__(self, *args, **kwargs)
        B.__init__(self, *args, **kwargs)
        print('C')


c = C()
b = B()


