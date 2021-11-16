# python-statistics-median

A drop-in replacement for Python's native [`statistics.median`](https://docs.python.org/3/library/statistics.html#statistics.median) using the [quickselect algorithm](https://en.wikipedia.org/wiki/Quickselect#Algorithm). Goal is to improve its performance since it sorts the data to find the median.

## To-do's
- [ ] Pass tests
- [ ] Implement other median-related functions:
  - [ ] `statistics.median_low`
  - [ ] `statistics.median_high`
  - [ ] `statistics.median_grouped`
