import random


def create_random_code():
    code = ''
    for i in range(6):
        code += str(random.randint(0, 9))
    return code
