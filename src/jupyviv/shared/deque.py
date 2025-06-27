import asyncio.events
import collections
from asyncio import QueueEmpty
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


# taken & adjusted from asyncio.Queue
# removes all features from Queue we don't need, adds opposite putleft
# analogously to existing append & change handler
class Deque(Generic[T]):
    def __init__(self):
        self._loop = asyncio.events.get_event_loop()
        self._getters = collections.deque()
        self._putters = collections.deque()
        self._deque = collections.deque[T]()
        self.change_handler: Optional[Callable[[collections.deque[T]], None]] = None

    def _wakeup_next(self, waiters):
        # wake up the next waiter (if any) that isn't cancelled.
        while waiters:
            waiter = waiters.popleft()
            if not waiter.done():
                waiter.set_result(None)
                break

    # change handler to allow side effects
    def _handle_change(self):
        if self.change_handler is not None:
            self.change_handler(self._deque)

    def empty(self):
        """Return True if the deque is empty, False otherwise."""
        return not self._deque

    def put(self, item: T):
        self._deque.append(item)
        self._handle_change()
        self._wakeup_next(self._getters)

    def putleft(self, item: T):
        self._deque.appendleft(item)
        self._handle_change()
        self._wakeup_next(self._getters)

    async def popleft(self) -> T:
        """Remove and return an item from the deque.
        If deque is empty, wait until an item is available."""
        while self.empty():
            getter = self._loop.create_future()
            self._getters.append(getter)
            try:
                await getter
            except:
                getter.cancel()  # Just in case getter is not done yet.
                try:
                    # Clean self._getters from canceled getters.
                    self._getters.remove(getter)
                except ValueError:
                    # The getter could be removed from self._getters by a
                    # previous put_nowait call.
                    pass
                if not self.empty() and not getter.cancelled():
                    # We were woken up by put_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._getters)
                raise
        return self.popleft_nowait()

    def popleft_nowait(self) -> T:
        """Remove and return an item from the deque.
        Return an item if one is immediately available, else raise QueueEmpty."""
        if self.empty():
            raise QueueEmpty
        item = self._deque.popleft()
        self._handle_change()
        self._wakeup_next(self._putters)
        return item
