# CLAUDE.md

## Pages (`src/app/pages/`)

Follow `.claude/pages-design.md` when building a page and `.claude/pages-comment.md` when commenting page files.

- `<name>/<name>.md`: one per page, for example `conversation/conversation.md`, based on `.claude/pages-doc.md`. It lists each workflow and the status every child VM gets at start / success / failure. When changing a page's state control, update its `.md` too.

## Components (`src/app/components/`)

Read the docs before using, changing, or creating a component. Follow `.claude/components-comment.md` for comments.

- `.claude/components-design.md`: how to build a component. It covers the controlled-component pattern, the file layout (`*-vm.ts`, `*-component.ts`, `*-component.html`), and how a page wires it up.
- `.claude/components-doc.md`: the template for a component's doc file.
- `<name>/<name>.md`: one per component, for example `composer/composer.md`. It lists the component's inputs, outputs, and two-way bindings, and how the parent page should handle them.

When creating a component, follow `.claude/components-design.md` and add a `<name>.md` based on `.claude/components-doc.md`. When changing a component's API, update its `.md` too.
