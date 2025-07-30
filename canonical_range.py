# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
from __future__ import division

from operator import lt, gt
from typing import Tuple, Sequence, Union, Iterator, TypeVar, Type

from canonical_interval import CanonicalInterval, RelativePosition


def contains(start, stop, step, element):
    # type: (int, int, int, int) -> bool
    if step == 0:
        raise ValueError('step cannot be 0')
    elif step > 0:
        return start <= element < stop and (element - start) % step == 0
    else:
        return stop < element <= start and (start - element) % (-step) == 0


def get_length(start, stop, step):
    # type: (int, int, int) -> int
    if step == 0:
        raise ValueError('step cannot be 0')
    elif step > 0:
        if start < stop:
            distance = stop - start
            n_step, remainder = divmod(distance, step)
            if remainder:
                return n_step + 1
            else:
                return n_step
        else:
            return 0
    else:
        if stop < start:
            distance = start - stop
            n_step, remainder = divmod(distance, -step)
            if remainder:
                return n_step + 1
            else:
                return n_step
        else:
            return 0


def canonicalize_stop(start, stop, step):
    # type: (int, int, int) -> int
    length = get_length(start, stop, step)
    return start + length * step


def slice_to_offset_range(sequence_length, slice_object):
    # type: (int, slice) -> Tuple[int, int, int]
    if sequence_length < 0:
        raise ValueError('sequence length must be non-negative')

    raw_start = slice_object.start
    raw_stop = slice_object.stop
    raw_step = slice_object.step

    # Extract `step` first
    if raw_step is None:
        step = 1
    elif isinstance(raw_step, int):
        step = raw_step
        if step == 0:
            raise ValueError('step must be non-zero')
    else:
        raise ValueError('step must be a non-zero int or None')

    # Extract `start_offset` and `stop_offset`
    if raw_start is None:
        if step > 0:
            raw_offset_start = 0
        else:
            raw_offset_start = sequence_length - 1
    elif isinstance(raw_start, int):
        start_index = raw_start
        if start_index < 0:
            raw_offset_start = start_index + sequence_length
        else:
            raw_offset_start = start_index
    else:
        raise ValueError('start must be an int or None')

    if raw_stop is None:
        if step > 0:
            raw_offset_stop = sequence_length
        else:
            raw_offset_stop = -1
    elif isinstance(raw_stop, int):
        stop_index = raw_stop
        if stop_index < 0:
            raw_offset_stop = stop_index + sequence_length
        else:
            raw_offset_stop = stop_index
    else:
        raise ValueError('stop must be an int or None')

    return raw_offset_start, canonicalize_stop(raw_offset_start, raw_offset_stop, step), step


CR = TypeVar('CR', bound='CanonicalizedRange')


class CanonicalRange(Sequence[int]):
    """A canonical range of integers. Ensures `step != 0, length >= 0, stop == start + length * step`.

    Attributes:
        start (int): The start value of the range (inclusive)
        stop (int): The stop value of the range (exclusive)
        step (int): The step between values
        length (int): The number of elements in the range

    Methods:
        __contains__(element): Check if element is in range
        __getitem__(index): Get item by index or slice
        __iter__(): Iterate through range values
        __len__(): Get length of range
        __reversed__(): Get reversed version of range
        extend(k): Extend range by k steps
    """
    __slots__ = ('start', 'stop', 'step', 'length')

    def __new__(cls, start, stop, step):
        # type: (Type[CR], int, int, int) -> CR
        if step != 0:
            length = get_length(start, stop, step)
            canonicalized_stop = start + length * step

            instance = super(CanonicalRange, cls).__new__(cls)
            instance.start = start
            instance.stop = canonicalized_stop
            instance.step = step
            instance.length = length
            return instance
        else:
            raise ValueError('start, stop, and step must be ints with step != 0')

    def __bool__(self):
        # type: () -> bool
        return self.length > 0

    def __contains__(self, value):
        # type: (object) -> bool
        if isinstance(value, int):
            return contains(self.start, self.stop, self.step, value)
        else:
            return False

    def __eq__(self, other):
        # type: (object) -> bool
        if isinstance(other, CanonicalRange):
            return (self.start, self.stop, self.step) == (other.start, other.stop, other.step)
        else:
            return False

    def __getitem__(self, index):
        # type: (Union[int, slice]) -> Union[int, CR]
        if isinstance(index, int):
            # Is it valid?
            if -self.length <= index < self.length:
                if index < 0:
                    offset = index + self.length
                else:
                    offset = index

                return self.start + offset * self.step
            else:
                raise IndexError('index out of range')
        elif isinstance(index, slice):
            new_offset_start, canonicalized_new_offset_stop, new_offset_step = slice_to_offset_range(self.length, index)

            if new_offset_step > 0:
                first_valid_offset = 0
                one_past_last_valid_offset = self.length
                comparator = lt
            else:
                first_valid_offset = self.length - 1
                one_past_last_valid_offset = -1
                comparator = gt

            current_offset_interval = CanonicalInterval(first_valid_offset, one_past_last_valid_offset, comparator)

            if new_offset_start == canonicalized_new_offset_stop:
                new_offset_start_relative_position = current_offset_interval.relative_position_of(new_offset_start)
                if new_offset_start_relative_position == RelativePosition.BEFORE:
                    intersection_offset_start = first_valid_offset
                    intersection_offset_stop = first_valid_offset
                elif new_offset_start_relative_position == RelativePosition.WITHIN:
                    intersection_offset_start = new_offset_start
                    intersection_offset_stop = new_offset_start
                else:
                    intersection_offset_start = one_past_last_valid_offset
                    intersection_offset_stop = one_past_last_valid_offset
            else:
                nonempty_new_offset_interval = CanonicalInterval(new_offset_start, canonicalized_new_offset_stop, comparator)
                before, within, after = current_offset_interval.three_way_split(nonempty_new_offset_interval)
                if within:
                    intersection_offset_start = within.start
                    intersection_offset_stop = within.stop
                elif before:
                    intersection_offset_start = first_valid_offset
                    intersection_offset_stop = first_valid_offset
                else:
                    intersection_offset_start = one_past_last_valid_offset
                    intersection_offset_stop = one_past_last_valid_offset

            new_start = self.start + self.step * intersection_offset_start
            new_stop = self.start + self.step * intersection_offset_stop
            new_step = self.step * new_offset_step

            return self.__class__(new_start, new_stop, new_step)
        else:
            raise TypeError('indices must be ints or slices')

    def __hash__(self):
        # type: () -> int
        return hash(self.__reduce__())

    def __iter__(self):
        # type: () -> Iterator[int]
        current = self.start
        while current != self.stop:
            yield current
            current += self.step

    def __len__(self):
        # type: () -> int
        return self.length

    def __reduce__(self):
        # type: () -> Tuple[Type[CR], Tuple[int, int, int]]
        return self.__class__, (self.start, self.stop, self.step)

    def __repr__(self):
        return '%s(%d, %d, %d)' % (self.__class__.__name__, self.start, self.stop, self.step)

    def __reversed__(self):
        # type: () -> CR
        """
        Creates a canonical, reversed version of the range.
        """
        if self.start == self.stop:
            return self.__class__(self.start, self.stop, -self.step)
        else:
            return self.__class__(self.stop - self.step, self.start - self.step, -self.step)

    def extend(self, k):
        # type: (int) -> Tuple[CR, CR]
        """
        Extends the range by k (k >= 0) steps and returns a tuple containing:

        - The canonicalized extended range (original range + k steps)
        - The canonicalized extension part (just the added k steps)
        """
        if k >= 0:
            extended_range_stop = self.stop + k * self.step

            extended_range = self.__class__(self.start, extended_range_stop, self.step)
            extended_by = self.__class__(self.stop, extended_range_stop, self.step)

            return extended_range, extended_by
        else:
            raise ValueError('k should be a non-negative int')
