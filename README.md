# The Snowbanker

This repository contains my attempt to have a computer make money for me on the stock market so I can spend my time doing other things. Here's my implementation plan:

- Write an underlying interface for reading the stock market and submitting trades.
- Implement multiple "strategies" that all use this interface.

By having multiple strategies, I figure I can pick and choose which ones I want to fire off at a specific time.

# File Breakdown

The files in this repository are as follows:

- `src/` contains all Python source files.
    - `src/sbi/` contains the underlying interface ("Snow Banker Interface") strategies will use.
    - `src/strats/` contains all implemented strategies.
