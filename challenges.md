# Challenges

1. **Environment setup.** macOS has no `python` command, only `python3`, and a
   mistyped `python -m python -m pip` failed. Resolved by activating `.venv`, where
   `python` works.

2. **`bool` is an `int` in Python.** `isinstance(True, int)` is `True`, so `True`
   passed as a time or capacity and behaved like `1`. `_is_valid_time` and
   `_is_valid_capacity` now exclude `bool` explicitly. `nan` and `inf` needed
   `math.isfinite`, because `nan >= 0` is `False` but `inf >= 0` is `True`.

3. **Strict versus lenient `active` check.** The spec only says "active". The
   acceptance matrix expects `False`, `0` and `None` to be inactive while truthy
   values count as active, so the filter is `if not partner.get('active')`. A first
   suggestion of `is True` was dropped for that reason.

4. **Cancellation edge cases.** A replayed event must not release capacity twice, and
   a cancellation for an order the partner does not hold must not corrupt workload.
   Decision: check `event_id` first, release only if the order is in
   `active_order_ids`, floor workload at 0, and still record the event ID so a replay
   of an unknown-order event is also ignored.

5. **Missing data versus zero.** The starter used `order.get('prep_minutes', 0)`,
   which silently turned missing data into zero, the same mistake the spec forbids
   for travel. The default was removed so a missing prep time is invalid.

6. **Diagnosing without the full source.** Early fixes were drafted from traceback
   snippets. They were replaced by a version built on the real `service.py` once it
   was available, keeping the original function names, signatures and return keys.
