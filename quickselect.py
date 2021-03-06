
from collections import deque
import random
from typing import Iterable


class StatisticsError(ValueError):
    pass


def partition(q: deque, left: int, right: int, pivot_index: int):
    """
    """
    pivot_value = q[pivot_index]
    q[pivot_index], q[right] = q[right], q[pivot_index]
    store_index = left
    for i, value in enumerate(q[j] for j in range(left, right)):
        if value < pivot_value:
            q[store_index], q[i] = q[i], q[store_index]
            store_index += 1
    q[right], q[store_index] = q[store_index], q[right]
    return store_index


def quickselect(l: Iterable, left: int, right: int, k: int):
    """
    """
    q = l
    if not isinstance(l, deque):
        q = deque(l)
    if left == right:
        return q[left]
    pivot_index = partition(q, left, right, random.randint(left, right))
    if k == pivot_index:
        return q[k]
    elif k < pivot_index:
        return quickselect(q, left, pivot_index-1, k)
    else:
        return quickselect(q, pivot_index+1, right, k)

def median(data):
    data = list(data)
    n = len(data)
    if n == 0:
        raise StatisticsError("No median for empty data")
    if n % 2 == 1:
        return quickselect(data, 0, n-1, n//2)
    else:
        i = n // 2
        return (quickselect(data, 0, n-1, i-1) + quickselect(data, 0, n-1, i)) / 2
