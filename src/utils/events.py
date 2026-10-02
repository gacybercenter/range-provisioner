"""
Event emitter and logging dispatcher for Range Provisioner.
Allows real-time streaming of provisioning events to CLI and Web UI (WebSockets/SSE).
"""
import asyncio
from datetime import datetime
from typing import Callable, List, Dict, Any, Optional
from threading import Lock


class ProvisionEvent:
    def __init__(self, level: str, message: str, endpoint: str = "", details: Optional[Any] = None):
        self.timestamp: str = datetime.now().isoformat()
        self.level: str = level  # INFO, SUCCESS, ERROR, DEBUG, WARNING
        self.message: str = str(message)
        self.endpoint: str = endpoint
        self.details: Optional[Any] = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "endpoint": self.endpoint,
            "details": self.details,
        }


class EventDispatcher:
    def __init__(self):
        self._listeners: List[Callable[[ProvisionEvent], None]] = []
        self._async_queues: List[asyncio.Queue] = []
        self._lock = Lock()
        self.event_history: List[ProvisionEvent] = []

    def subscribe(self, listener: Callable[[ProvisionEvent], None]) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[ProvisionEvent], None]) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def register_async_queue(self, queue: asyncio.Queue) -> None:
        with self._lock:
            if queue not in self._async_queues:
                self._async_queues.append(queue)

    def unregister_async_queue(self, queue: asyncio.Queue) -> None:
        with self._lock:
            if queue in self._async_queues:
                self._async_queues.remove(queue)

    def dispatch(self, level: str, message: str, endpoint: str = "", details: Optional[Any] = None) -> ProvisionEvent:
        event = ProvisionEvent(level=level, message=message, endpoint=endpoint, details=details)
        with self._lock:
            self.event_history.append(event)
            if len(self.event_history) > 2000:
                self.event_history = self.event_history[-2000:]
            listeners = list(self._listeners)
            queues = list(self._async_queues)

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                pass

        for q in queues:
            try:
                q.put_nowait(event)
            except Exception:
                pass

        return event

    def clear_history(self) -> None:
        with self._lock:
            self.event_history.clear()


dispatcher = EventDispatcher()
