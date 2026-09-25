# PawPass

Pet Care Management System built using Frappe Framework.

## Features

* Pet and owner management
* Stay Card management
* Attendant management
* Service and billing management
* Automated email notifications
* Role-based permissions
* Custom Client Scripts and server-side validations
* Scheduled background jobs
* Custom API and webhook integration

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH

bench get-app $URL_OF_THIS_REPO --branch version-16

bench install-app pawpass
```

## Contributing

This app uses `pre-commit` for code formatting and linting.

```bash
cd apps/pawpass

pre-commit install
```

Pre-commit is configured with:

* ruff
* eslint
* prettier
* pyupgrade

## Internal Notes

### B2C — Document Lifecycle

`validate()` should be used for validation and calculations, not for permanent updates to related documents. Updating the Pet inside `validate()` can happen multiple times because validation may run more than once.

The Pet's stay count is therefore updated in `on_submit()`, so it changes only when the Stay Card is actually submitted.

### B2D — Concurrent Updates

Frappe checks the document's `modified` timestamp before saving. If another user or process has already modified the document, Frappe stops the save to prevent an older version from overwriting newer data.

### D2 — Data Leakage

`frappe.get_all()` ignores normal DocType permissions, so using it in a whitelisted method can expose records to users who should not have access.

`frappe.get_list()` is safer for user-facing APIs because it applies permission filters. Sensitive fields such as `owner_email` and `owner_phone` are also removed for users who should not see them.

### E1 — `on_update()` Recursion

Calling `self.save()` inside `on_update()` causes `on_update()` to run again and can create recursion.

For direct database updates, `frappe.db.set_value()` can be used when appropriate.

### E3 — `get_value()` vs `get_doc()`

When only one field is required, `frappe.db.get_value()` is more efficient than loading the complete document with `frappe.get_doc()`.

For example, reading `reminder_days_before_checkout` from PawPass Settings only requires the single field.

### H1 — Async Client Calls

`frappe.call()` is asynchronous. Using it inside the `validate` client event can cause the form save process to continue before the API response is available.

Async data fetching should be done earlier, such as in `onload` or `refresh`, when the data needs to be available before validation.

### K2 — N+1 Queries

An N+1 problem happens when one query gets the main records and another query is executed for every record inside a loop.

Instead of fetching each Attendant with `frappe.get_doc()` inside the loop, all required Attendants can be fetched in one query and stored in a dictionary for lookup.

This reduces unnecessary database queries and improves performance.

## License

MIT
