# Public and personal setup documentation

`README.WINDOWS.md` is the public setup guide. It uses relative paths,
environment variables and generic example locations. Machine-specific paths
belong in the ignored `README.WINDOWS.personal.md` or `.private/` directory.

Generate the personal guide from the public source with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\New-PersonalWindowsGuide.ps1 -Msys2Root 'C:\msys64'
```

Set the MSYS2 argument to your actual installation root. The personal document
contains your local paths; do not force-add it, upload it to an issue or attach
it to a public support request. Regenerate it when the public guide changes.
Its generator refuses to write the file unless Git confirms it is ignored.

Before publishing, run:

```powershell
python tests/windows/check_public_privacy.py
```

This check catches non-generic Windows profile paths and common computer names
in tracked text. It does not replace a review of staged changes, author metadata,
screenshots, archives or binary artifacts. Runtime build metadata and raw audit
results remain local under ignored `bin/` and `validation-results/`; review and
generalize copies before including them in a public evidence record.

## Historical evidence

Public audit records have machine paths replaced with generic locations. A path
in such a record is illustrative, not an instruction to access the original
machine. These redactions do not represent a new scientific validation run.
Numerical results, compiler settings and original recorded artifact hashes are
preserved; changed JSON/document bytes naturally have different hashes.
Private recovery copies retain the original records locally.

## After a repository history cleanup

Development commit IDs change when personal data is removed from history.
Use a fresh clone for ongoing work. Do not merge or force-push an older clone
or restore an old bundle into a public remote; that can reintroduce the removed
history. The upstream tracking branch and upstream attribution are preserved.

Rewritten branches cannot erase other people's existing clones, and GitHub can
retain cached commit views. GitHub documents the remaining support process for
[removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
