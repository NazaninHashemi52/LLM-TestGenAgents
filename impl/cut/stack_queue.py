"""Stack and queue data structures — a stateful CUT for test generation experiments."""


class EmptyError(Exception):
    """Raised when reading from or removing from an empty container."""


class FullError(Exception):
    """Raised when adding to a container that has reached its capacity."""


def _check_capacity(capacity):
    """Validate an optional capacity argument."""
    if capacity is None:
        return
    if not isinstance(capacity, int) or isinstance(capacity, bool):
        raise TypeError("capacity must be an int or None")
    if capacity <= 0:
        raise ValueError("capacity must be positive")


# ---------------------------------------------------------------------------
# Stack (LIFO)
# ---------------------------------------------------------------------------

class Stack:
    """A last-in, first-out stack with an optional maximum capacity."""

    def __init__(self, capacity=None):
        _check_capacity(capacity)
        self._items = []
        self._capacity = capacity

    def push(self, item):
        """Push item on top of the stack.

        Raises:
            FullError: if the stack is at capacity.
        """
        if self.is_full():
            raise FullError("stack is full")
        self._items.append(item)

    def pop(self):
        """Remove and return the top item.

        Raises:
            EmptyError: if the stack is empty.
        """
        if self.is_empty():
            raise EmptyError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        """Return the top item without removing it.

        Raises:
            EmptyError: if the stack is empty.
        """
        if self.is_empty():
            raise EmptyError("peek at empty stack")
        return self._items[-1]

    def is_empty(self):
        """Return True if the stack has no items."""
        return len(self._items) == 0

    def is_full(self):
        """Return True if the stack has reached its capacity (never for unbounded)."""
        return self._capacity is not None and len(self._items) >= self._capacity

    def clear(self):
        """Remove all items."""
        self._items.clear()

    def to_list(self):
        """Return the items from bottom to top as a new list."""
        return list(self._items)

    def __len__(self):
        return len(self._items)

    def __contains__(self, item):
        return item in self._items


# ---------------------------------------------------------------------------
# Queue (FIFO) — implemented as a circular buffer
# ---------------------------------------------------------------------------

class Queue:
    """A first-in, first-out queue backed by a growable circular buffer."""

    _INITIAL_SIZE = 4

    def __init__(self, capacity=None):
        _check_capacity(capacity)
        self._capacity = capacity
        self._buffer = [None] * self._INITIAL_SIZE
        self._head = 0
        self._size = 0

    def _grow(self):
        """Double the internal buffer, unrolling the circular layout."""
        old = self._buffer
        n = len(old)
        self._buffer = [old[(self._head + i) % n] for i in range(self._size)]
        self._buffer.extend([None] * (n * 2 - self._size))
        self._head = 0

    def enqueue(self, item):
        """Add item to the back of the queue.

        Raises:
            FullError: if the queue is at capacity.
        """
        if self.is_full():
            raise FullError("queue is full")
        if self._size == len(self._buffer):
            self._grow()
        tail = (self._head + self._size) % len(self._buffer)
        self._buffer[tail] = item
        self._size += 1

    def dequeue(self):
        """Remove and return the item at the front of the queue.

        Raises:
            EmptyError: if the queue is empty.
        """
        if self.is_empty():
            raise EmptyError("dequeue from empty queue")
        item = self._buffer[self._head]
        self._buffer[self._head] = None
        self._head = (self._head + 1) % len(self._buffer)
        self._size -= 1
        return item

    def front(self):
        """Return the front item without removing it.

        Raises:
            EmptyError: if the queue is empty.
        """
        if self.is_empty():
            raise EmptyError("front of empty queue")
        return self._buffer[self._head]

    def is_empty(self):
        """Return True if the queue has no items."""
        return self._size == 0

    def is_full(self):
        """Return True if the queue has reached its capacity (never for unbounded)."""
        return self._capacity is not None and self._size >= self._capacity

    def to_list(self):
        """Return the items from front to back as a new list."""
        n = len(self._buffer)
        return [self._buffer[(self._head + i) % n] for i in range(self._size)]

    def __len__(self):
        return self._size


# ---------------------------------------------------------------------------
# Helper using a Stack
# ---------------------------------------------------------------------------

_BRACKET_PAIRS = {")": "(", "]": "[", "}": "{"}


def is_balanced(expression):
    """Return True if all (), [] and {} brackets in expression are balanced.

    Non-bracket characters are ignored.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a str")
    stack = Stack()
    for ch in expression:
        if ch in "([{":
            stack.push(ch)
        elif ch in _BRACKET_PAIRS:
            if stack.is_empty() or stack.pop() != _BRACKET_PAIRS[ch]:
                return False
    return stack.is_empty()
