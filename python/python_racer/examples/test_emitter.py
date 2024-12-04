from python_racer.events.emitter import EventEmitter
from dataclasses import dataclass
import time

@dataclass
class Counter:
    value: int

def test_scan():
    print("\nTesting scan...")
    # Create event stream
    numbers = EventEmitter[int]()
    
    # Create state stream that accumulates numbers
    sum_stream = numbers.scan(
        initial=0,
        f=lambda state, event: state + event
    )
    
    # Subscribe to see results
    sum_stream.subscribe(lambda x: print(f"Sum is now: {x}"))
    
    # Emit some numbers
    for i in range(5):
        print(f"Emitting: {i}")
        numbers.emit(i)
        
def test_map():
    print("\nTesting map...")
    numbers = EventEmitter[int]()
    doubled = numbers.map(lambda x: x * 2)
    doubled.subscribe(lambda x: print(f"Doubled: {x}"))
    
    for i in range(5):
        print(f"Emitting: {i}")
        numbers.emit(i)
        
def test_filter():
    print("\nTesting filter...")
    numbers = EventEmitter[int]()
    evens = numbers.filter(lambda x: x % 2 == 0)
    evens.subscribe(lambda x: print(f"Even number: {x}"))
    
    for i in range(5):
        print(f"Emitting: {i}")
        numbers.emit(i)
        
def test_combine():
    print("\nTesting combine...")
    a = EventEmitter[str]()
    b = EventEmitter[int]()
    
    combined = EventEmitter.combine(a, b)
    combined.subscribe(lambda x: print(f"Combined: {x}"))
    
    print("Emitting 'hello' to a")
    a.emit("hello")
    print("Emitting 42 to b")
    b.emit(42)
    print("Emitting 'world' to a")
    a.emit("world")
    print("Emitting 123 to b")
    b.emit(123)

def main():
    test_scan()
    test_map()
    test_filter()
    test_combine()

if __name__ == "__main__":
    main() 