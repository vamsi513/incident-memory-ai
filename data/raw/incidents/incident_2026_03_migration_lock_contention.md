# Schema Migration Lock Blocked Writes

## Summary
A routine database schema migration took an exclusive lock on the orders table for 35 minutes, blocking all order writes for the duration.

## Impact
Customers could browse and add items to cart normally, but every checkout attempt during the window failed with a generic error. Checkout conversion dropped to zero for 35 minutes.

## Root Cause
The migration added a new column with a non-null default value to the orders table. On the database engine in use, adding a column with a default requires rewriting every existing row under an exclusive table lock, which is fast on a small table but took over half an hour on the orders table's actual size. This was not caught in staging because the staging orders table has a small fraction of production's row count.

## Mitigation
On-call identified the long-running migration via the database's active-queries view and canceled it, releasing the lock and restoring checkout immediately. The column was later added successfully using a safer multi-step approach (add nullable column, backfill in batches, then add the constraint).

## Follow-up Actions
- Add a migration linter that flags "add column with non-null default" on large tables
- Load staging's orders table with a production-representative row count before running migration rehearsals
- Document the safe multi-step pattern for adding non-null columns to large tables
