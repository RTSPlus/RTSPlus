from collections import deque


def km2ft(km):
    return km * 0.621371 * 5280


def km2mi(km):
    return km * 0.621371


# https://stackoverflow.com/a/36586925
def chunks(iterable, chunk_size=3, overlap=0):
    # we'll use a deque to hold the values because it automatically
    # discards any extraneous elements if it grows too large
    if chunk_size < 1:
        raise Exception("chunk size too small")
    if overlap >= chunk_size:
        raise Exception("overlap too large")
    queue = deque(maxlen=chunk_size)
    it = iter(iterable)
    i = 0
    try:
        # start by filling the queue with the first group
        for i in range(chunk_size):
            queue.append(next(it))
        while True:
            yield list(queue)
            # after yielding a chunk, get enough elements for the next chunk
            for i in range(chunk_size - overlap):
                queue.append(next(it))
    except StopIteration:
        # if the iterator is exhausted, yield any remaining elements
        i += overlap
        if i > 0:
            yield list(queue)[-i:]
