"""
STUDY version of the demo target (for YOUR eyes, not the agent).

Same bug as buggy_script_BROKEN.py, but with a comment marking exactly where
it is and why it's wrong. Use this to study. Do NOT run the agent on this one:
the comment hands the model the answer.
"""

import heapq


class RunningMedian:
    def __init__(self):
        self.low = []   # max-heap (stored as negated values)
        self.high = []  # min-heap

    def add(self, num):
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))

        if len(self.low) < len(self.high):
            # BUG: the value popped from `high` is a real (positive) value,
            # but `low` stores negated values. Pushing it without the leading
            # minus corrupts the max-heap ordering silently. Correct line is:
            #     heapq.heappush(self.low, -heapq.heappop(self.high))
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
