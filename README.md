# `canonical-range`

A Python implementation of a **canonical range** (where `step != 0, length >= 0, stop == start + length * step`) with enhanced functionality compared to Python's built-in `range`.

## Features

- **Canonical Representation**: Always stores ranges in a consistent mathematical form (
  `step != 0, length >= 0, stop == start + length * step`)
- **Full Sequence Protocol**: Implements all Sequence methods (`__getitem__`, `__len__`, etc.)
- **Type Safety**: Comprehensive type hints throughout
- **Memory Efficient**: Uses `__slots__` for reduced memory footprint

## Installation

```bash
pip install canonical-range
```

## Basic Usage

```python
from canonical_range import CanonicalRange


def start_stop_step(canonical_range):
    return canonical_range.start, canonical_range.stop, canonical_range.step


# Range contains the elements [10, 13, 16, 19]
# Canonicalized to CanonicalRange(10, 22, 3)
r1 = CanonicalRange(10, 20, 3)
assert start_stop_step(r1) == (10, 22, 3)
assert r1.length == 4

# Range contains the elements [10, 13, 16, 19, 22]
# Canonicalized to CanonicalRange(10, 25, 3)
r2 = CanonicalRange(10, 23, 3)
assert start_stop_step(r2) == (10, 25, 3)
assert r2.length == 5

# Range contains the elements [20, 17, 14, 11]
# Canonicalized to CanonicalRange(20, 8, -3)
r3 = CanonicalRange(20, 10, -3)
assert start_stop_step(r3) == (20, 8, -3)
assert r3.length == 4

# Extending ranges
assert repr(CanonicalRange(1, 5, 1).extend(2)) == '(CanonicalRange(1, 7, 1), CanonicalRange(5, 7, 1))'
assert repr(
    CanonicalRange(1, 5, 1).extend(0)) == '(CanonicalRange(1, 5, 1), CanonicalRange(5, 5, 1))'  # Empty extension

# Range is empty
assert not CanonicalRange(5, 5, 1)
assert not CanonicalRange(5, 5, -1)
assert not CanonicalRange(5, 4, 1)
assert not CanonicalRange(5, 6, -1)

# Indexing and slicing
r4 = CanonicalRange(0, 10, 1)

# Empty slice
assert r4[1:1] == CanonicalRange(1, 1, 1)
assert not r4[1:1]

assert r4[1:0] == CanonicalRange(1, 1, 1)
assert not r4[1:0]

# Range contains the elements [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
assert r4[0] == r4[-10] == 0
assert r4[-1] == r4[9] == 9
assert all(i in r4 for i in range(10))
assert -1 not in r4
assert 10 not in r4

# Sliced range contains the elements [2, 3, 4]
assert start_stop_step(r4[2:5]) == (2, 5, 1)

# Sliced range contains the elements [2, 4]
assert start_stop_step(r4[2:5:2]) == (2, 6, 2)

# Sliced range contains the elements [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert start_stop_step(r4[::-1]) == start_stop_step(reversed(r4)) == (9, -1, -1)
assert 9 in r4[::-1]
assert 0 in r4[::-1]
assert -1 not in r4[::-1]

# Sliced range contains the elements [5, 3]
assert start_stop_step(r4[5:2:-2]) == (5, 1, -2)

# For ranges,
# If step > 0,
# If start < -length, it gets clamped up to 0
# If start > length, it gets clamped down to length
# If stop < -length, it gets clamped up to 0
# If stop > length, it gets clamped down to length
# We then do canonicalization on top of this
# Examples:
# range(10)[-14:-16:2] -> range(0, 0, 2)
# range(10)[-14:-12:2] -> range(0, 0, 2)
# range(10)[-14:6:4] -> range(0, 6, 4) -> range(0, 8, 4)
# range(10)[-14:28:21] -> range(0, 10, 21) -> range(0, 21, 21)
# range(10)[14:-14:2] -> range(10, 0, 2) -> range(10, 10, 2)
# range(10)[14:2:2] -> range(10, 2, 2) -> range(10, 10, 2)
# range(10)[14:12:2] -> range(10, 10, 2)
# range(10)[14:16:2] -> range(10, 10, 2)
assert start_stop_step(r4[-14:-16:2]) == (0, 0, 2)
assert start_stop_step(r4[-14:-12:2]) == (0, 0, 2)
assert start_stop_step(r4[-14:6:4]) == (0, 8, 4)
assert start_stop_step(r4[-14:28:21]) == (0, 21, 21)
assert start_stop_step(r4[14:-14:2]) == start_stop_step(r4[14:2:2]) == start_stop_step(r4[14:12:2]) == start_stop_step(r4[14:16:2]) == (10, 10, 2)

# If step < 0,
# If start < -length, it gets clamped up to -1
# If start > length - 1, it gets clamped down to length - 1
# If stop < -length, it gets clamped up to -1
# If stop > length - 1, it gets clamped down to length - 1
# We then do canonicalization on top of this
# Examples:
# range(10)[-14:-16:-2] -> range(-1, -1, -2)
# range(10)[-14:-12:-2] -> range(-1, -1, -2)
# range(10)[-14:6:-2] -> range(-1, 6, -2) -> range(-1, -1, -2)
# range(10)[-14:6:-4] -> range(-1, 6, -4) -> range(-1, -1, -4)
# range(10)[-14:28:-21] -> range(-1, 9, -21) -> range(-1, -1, -21)
# range(10)[14:-14:-2] -> range(9, -1, -2)
# range(10)[14:2:-2] -> range(9, 2, -2) -> range(9, 1, -2)
# range(10)[14:12:-2] -> range(9, 9, -2)
# range(10)[14:16:-2] -> range(9, 9, -2)
assert start_stop_step(r4[-14:-16:-2]) == start_stop_step(r4[-14:-12:-2]) == start_stop_step(r4[-14:6:-2]) == (-1, -1, -2)
assert start_stop_step(r4[-14:6:-4]) == (-1, -1, -4)
assert start_stop_step(r4[-14:28:-21]) == (-1, -1, -21)
assert start_stop_step(r4[14:-14:-2]) == (9, -1, -2)
assert start_stop_step(r4[14:2:-2]) == (9, 1, -2)
assert start_stop_step(r4[14:12:-2]) == start_stop_step(r4[14:16:-2]) == (9, 9, -2)
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).