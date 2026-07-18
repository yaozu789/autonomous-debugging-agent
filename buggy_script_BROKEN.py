"""
DEMO TARGET for the Autonomous Debugging Agent.

Computes the running median of a stream of numbers using two heaps (a classic
interview-style algorithm). It contains a genuine, SILENT bug: it runs to
completion, prints plausible-looking output, and only the final assertion
reveals the numbers are wrong. That kind of bug can't be fixed by reading a
stack trace, so the agent has to run it, compare output to expected, and reason
about the heap logic.

Point the agent at THIS file:
    python agent.py --file buggy_script_BROKEN.py
"""

import heapq


class RunningMedian:
    def __init__(self):
        self.low = []   # max-heap (stored as negated values)
        self.high = []  # min-heap

    def add(self, num):
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))

        if len(self.high) > len(self.low):
            heapq.heappush(self.low, heapq.heappop(self.high))

    def median(self):
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2


if __name__ == "__main__":
    stream = [5, 15, 1, 3, 8, 7, 9, 10, 2, 6, 4, 12, 11, 13, 14]
    rm = RunningMedian()
    medians = []
    for n in stream:
        rm.add(n)
        medians.append(rm.median())

    print("Stream:", stream)
    print("Running medians:", medians)

    import statistics
    expected = [statistics.median(stream[: i + 1]) for i in range(len(stream))]
    print("Expected:", expected)
    assert medians == expected, "Running medians do not match expected values!"
    print("All medians correct.")
