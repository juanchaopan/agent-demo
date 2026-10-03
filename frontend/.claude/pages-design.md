# Page Design

A page only integrates: it owns state, calls the API, and wires child components.

- **Template**: page owns page-level layout (flex, grid, spacing, positioning); child components bound via `[input]`, `[(model)]`, `(output)` only.
- **State**: only these three kinds.
  - `输入`: route params via `input()`.
  - `XxxVM`: one signal per child component, typed as its VM. All display state (status, error, data) lives in the VM of the child that shows it.
  - `控制器`: plain private fields (not signals) for things nobody observes, e.g. `AbortController`.
- **Everything else** (other signals, DOM behavior like scrolling or focus) goes into the child component that owns it; extract one if needed.
- **Functions**, three kinds:
  - **Entry points**: `effect`s watching `输入`, their `onCleanup` (aborts every `控制器` on input change or page destroy; no `DestroyRef.onDestroy`), and one handler per child output. They only guard and call workflows. If two actions are the same operation with different starting points, merge them into one output with a parameter.
  - **Workflows**: one function per API operation, each with its own try/catch; its main logic may call a service. Only workflows set VM status at start / success / failure, and each maps to a table in the page's `<name>.md`. Each workflow has its own `控制器`, aborts its previous one first, and passes the signal to every request.
  - **Callbacks**: local private functions a workflow calls or passes to the API. They never decide a workflow's start / success / failure.
