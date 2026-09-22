# Thermal data layer

PR1 centralizes API methods, models, constants, query keys and mutation options.
The consumer migration (PR2) follows the other domain foundations and the
`GroupedDataTable` refactor.

Temporary compatibility points:

- The route's `-utils.ts` preserves positional helpers and re-exports. Remove them
  after migrating their consumers; matrix column labels remain presentation code.
- List responses normalize IDs; individual and mutation responses retain server
  casing. Align IDs when migrating consumers and cache updates together.
- Legacy form types are retained, including optional versioned fields. Reconcile
  them with nullable API fields during the form migration.
- The existing area-list key remains shared with reserves. `EXTERNALLY_MUTATED`
  stays until legacy pages, table mode and other study-edit paths invalidate it.
- Mutation options only declare keys and API functions. Consumer hooks will own
  cache updates, rollback and dependent-query invalidation after the table's
  optimistic-state ownership is resolved.

PR2 should select cluster details from the list, preserve direct navigation and
unsaved form edits, and remove migrated Redux server-data dependencies only when
their shared synthesis consumers have replacements.
