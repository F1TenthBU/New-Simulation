from typing import Generic, TypeVar, Callable, List, Any, Tuple
from dataclasses import dataclass, field
import multiprocessing as mp
import threading

T = TypeVar('T')
S = TypeVar('S')  # State type
U = TypeVar('U')  # For map return type

@dataclass
class EventEmitter(Generic[T]):
    """Base class for discrete event emitters with value replay."""
    subscribers: List[Callable[[T], None]] = field(default_factory=list)
    latest_value: T = field(default=None)  # Track latest value
    
    def subscribe(self, callback: Callable[[T], None]) -> None:
        """Subscribe to events, immediately receiving latest value if available."""
        self.subscribers.append(callback)
        if self.latest_value is not None:
            callback(self.latest_value)
        
    def emit(self, arg: T) -> None:
        """Emit a new event, updating latest value and notifying subscribers."""
        self.latest_value = arg
        for subscriber in self.subscribers:
            subscriber(arg)
            
    def map(self, f: Callable[[T], U]) -> 'EventEmitter[U]':
        """Transform events using pure function f."""
        result = EventEmitter[U]()
        self.subscribe(lambda x: result.emit(f(x)))
        return result
    
    def filter(self, pred: Callable[[T], bool]) -> 'EventEmitter[T]':
        """Filter events based on predicate."""
        result = EventEmitter[T]()
        self.subscribe(lambda x: result.emit(x) if pred(x) else None)
        return result
    
    def scan(self, initial: S, f: Callable[[S, T], S]) -> 'EventEmitter[S]':
        """Transform an event stream into a state stream."""
        result = EventEmitter[S]()
        result.emit(initial)  # Emit initial state immediately
        
        def on_event(event: T):
            new_state = f(result.latest_value, event)
            result.emit(new_state)
            
        self.subscribe(on_event)
        return result

    def apply_patches(self, *patch_emitters: 'EventEmitter[Callable[[T], T]]') -> 'EventEmitter[T]':
        """
        Apply multiple streams of patches to the current stream.
        Used for stateless state management, particularly in view transforms.
        """
        result = EventEmitter[T]()
        
        # When self emits, update result directly
        self.subscribe(result.emit)
        
        # When any patch_emitter emits, apply change to latest value
        def patch_latest(change_fn: Callable[[T], T]):
            if result.latest_value is not None:
                result.emit(change_fn(result.latest_value))
        
        # Subscribe to all patch emitters
        for patch_emitter in patch_emitters:
            patch_emitter.subscribe(patch_latest)
            
        return result
    
    @staticmethod
    def combine(*emitters: 'EventEmitter') -> 'EventEmitter[Tuple]':
        """Combine multiple event streams into one synchronized stream."""
        result = EventEmitter[Tuple]()
        
        # Store latest values for each emitter
        latest = [None] * len(emitters)
        
        def make_handler(index: int):
            def handle_event(value: Any):
                latest[index] = value
                if all(v is not None for v in latest):
                    result.emit(tuple(latest))
            return handle_event
        
        # Subscribe to all emitters
        for i, emitter in enumerate(emitters):
            emitter.subscribe(make_handler(i))
            
        return result
    
    @staticmethod
    def merge(*emitters: 'EventEmitter') -> 'EventEmitter':
        """Merge multiple event streams into one, emitting events as they arrive."""
        result = EventEmitter()
        
        for emitter in emitters:
            emitter.subscribe(result.emit)
            
        return result
    
    @staticmethod
    def from_queue(queue: mp.Queue) -> 'EventEmitter[T]':
        """Create an event emitter that emits values from a queue as they arrive."""
        emitter = EventEmitter[T]()
        
        def queue_reader():
            while True:
                try:
                    value = queue.get()  # Blocks until data is available
                    emitter.emit(value)
                except (EOFError, OSError):
                    # Queue was closed or process ended
                    break
                except Exception as e:
                    print(f"Queue error: {e}")
        
        # Start reader thread
        threading.Thread(target=queue_reader, daemon=True).start()
        
        return emitter
