from typing import Collection, Generator, TypeVar, List

T = TypeVar('T')


def iter_batches(iterable: Collection[T], n: int = 1) -> Generator[List[T], None, None]:
    """Partition a collection into batches of size n.

    :param iterable: The collection to partition.
    :param n: The size of each batch.
    """
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx:min(ndx + n, length)]
