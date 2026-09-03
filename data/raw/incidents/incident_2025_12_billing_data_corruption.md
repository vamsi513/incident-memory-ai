# Billing Calculation Data Corruption

## Summary
A database migration with an incorrect default value silently corrupted tax calculations for orders placed over a 6-hour window before being caught.

## Impact
Approximately 1,400 orders were billed with an incorrect tax amount, most undercharging customers by a small percentage rather than overcharging. No orders were charged more than the correct amount by more than a rounding difference. The issue was caught by a routine reconciliation job rather than a customer report.

## Root Cause
A migration added a new tax_region_code column to the orders table with a default value of the wrong region code (an existing region rather than "unknown"), intended as a temporary placeholder to be backfilled by a separate job. The backfill job was scheduled to run after the migration but was accidentally left disabled from a prior test run. Orders placed before the backfill ran inherited the wrong default region code and were billed using that region's tax rate instead of their actual region's rate.

## Mitigation
The nightly billing reconciliation job flagged a tax-amount anomaly for the affected time window. The team ran the backfill job manually to correct the region codes, recalculated tax for the affected orders, and issued corrected invoices and refunds where customers had been undercharged.

## Follow-up Actions
- Require backfill jobs tied to a migration to run automatically as part of the same deployment, not as a manual follow-up step
- Add a data-quality check that flags any row still holding a migration's placeholder default value after 24 hours
- Add tax-amount anomaly detection with a tighter alert threshold than the current reconciliation job
