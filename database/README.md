# Local PostgreSQL Setup for RavenStack

This folder contains the local PostgreSQL scripts for archive 1.

## Script order

1. `01_reset_and_schema_ravenstack.sql`
2. `02_import_ravenstack_psql.sql` or `02_import_ravenstack_query_editor.sql`
3. `03_create_ravenstack_training_views.sql`
4. `04_validation_queries.sql`

## Recommended flow

1. Create an empty PostgreSQL database locally.
2. Run the reset-and-schema script.
3. Import the CSV files with `psql` using the import script, or run the query-editor script if the server can read the file path.
4. Create the training views.
5. Run the validation queries.

## Final training source

Use `v_ravenstack_training_dataset` as the final source for model training.

It produces one row per account and already aggregates subscriptions, usage, support tickets, and churn history.

## Notes

- `feature_usage` uses a surrogate `id` primary key because `usage_id` is not unique in the source CSV.
- The aggregated view avoids double counting by summarizing each child table separately before joining them back to `accounts`.