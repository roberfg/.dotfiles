---
name: verify-commit-messages
description: Use when the user asks to prepare Git commit messages or file groupings from new and modified changes, especially Conventional Commits. Always write proposed commit messages in English and never execute Git staging or commit operations.
---

# Prepare Commit Messages

## Purpose

Inspect only the current repository changes and generate coherent file lists and
English commit messages that follow the Conventional Commits 1.0.0
specification. The purpose is to prepare commits, not to review or correct
messages from existing commits.

This skill is read-only with respect to Git history and the index. It may read
repository state, but it must not stage, commit, reset, checkout, merge, rebase,
stash, push, or delete files.

## When to use

Use this skill when the user mentions any of the following:

- Preparing commit messages from current changes.
- Listing files to add to each commit.
- Grouping new and modified files into commits.
- Proposing Conventional Commit messages.
- Preparing stage-file groupings without staging them.

Trigger on Spanish and English requests, including phrases such as:

- `prepara los commits`
- `genera mensajes de commit`
- `lista los archivos para agregar`
- `organiza los archivos en commits`
- `propón un mensaje de commit`
- `organiza los stage files`
- `check commit messages`
- `prepare commit messages`
- `list files to stage`
- `group changes into commits`

## Workflow

1. Inspect the repository state with read-only commands:
   - `git status --short`
   - `git diff --stat`
   - `git diff`
   - `git diff --cached --stat`
   - `git diff --cached`
2. Identify all current tracked, untracked, staged, and unstaged files. Treat
   files absent from `HEAD` and current modifications as changes to prepare.
3. Do not evaluate, correct, or propose replacements for messages in `git log`.
   Existing history may be inspected only when necessary to understand file
   ownership or repository conventions.
4. Check current diffs and relevant untracked files for secrets, credentials,
   private keys, tokens, or sensitive values. Warn clearly and do not include
   files exposing secrets in a proposed group.
5. Group current files by one coherent change. Keep unrelated pre-existing
   worktree changes outside the proposed groups, and state any ambiguity rather
   than inventing file ownership.
6. For every proposed group, list the exact file paths to add or stage. Do not
   use directory-only placeholders, invented paths, or claims that files are
   already staged.
7. Propose one English commit message for every group and validate it against
   the Conventional Commits format.
8. If the changes are empty, state that there are no new or modified files to
   prepare.

## Conventional Commits format

Use this structure:

```text
<type>[optional scope][optional !]: <description>
```

Examples:

```text
feat(auth): add password reset flow
fix(parser): handle empty card names
refactor(storage): separate collection and export directories
docs(readme): document the new export workflow
test(parser): cover malformed deck entries
chore(deps): update scraping dependencies
```

Apply these rules:

- The `type` is lowercase.
- Use a lowercase, concise scope when it adds useful context.
- Put a colon and one space after the optional scope.
- Write the description in English.
- Start the description with a lowercase letter.
- Use imperative mood, such as `add`, `fix`, `move`, `document`, or `update`.
- Do not end the description with a period.
- Use `!` only for a breaking change and explain the impact in the body or
  footer when relevant.
- Prefer a specific scope over a generic scope such as `misc`.

Common types:

- `feat`: add user-visible functionality.
- `fix`: correct faulty behavior.
- `refactor`: change implementation without changing behavior.
- `docs`: change documentation only.
- `test`: add or change tests only.
- `build`: change build system or external dependencies.
- `ci`: change continuous integration configuration.
- `perf`: improve performance.
- `style`: change formatting without changing behavior.
- `chore`: maintenance that does not fit another type.

## Required output

Answer in Spanish unless the user requests another language, but always keep
the following content in English:

- Commit messages.
- Pull request titles.
- Changelog entries.
- Suggested commit bodies and footers.

Output only the proposed groups for current changes. Do not include an audit or
evaluation of past commit messages. Use this structure unless the user asks for
a different format:

```text
Commit 1: <English Conventional Commit message>

Files to add:
- path/to/file

Files to modify:
- path/to/another-file
```

Use only the sections that apply. `Files to add` contains untracked files and
`Files to modify` contains tracked files with current changes, whether staged
or unstaged. If a group contains both, include both sections. If changes should
be committed together, provide one group. If they should be split, briefly
explain the responsibility of each group in Spanish before its English message
and exact paths.

When a file is ambiguous, do not silently include it. Add an `Ambiguities`
section after the proposed groups with the exact path and the reason it needs
confirmation.

## Safety

- Never run `git add` or any other command that changes the index.
- Never run `git commit`, amend, reset, checkout, merge, rebase, stash, push, or
  branch deletion.
- Never modify files as part of this skill.
- Do not include unrelated changes merely because they are present in the
  worktree.
- Do not invent files or claim that a file is staged.
- Do not evaluate or report problems in historical commit messages unless the
  user explicitly asks for a history review instead of preparing current
  changes.
- If the repository state is ambiguous, list the ambiguity and avoid including
  the affected file in a definitive group.
