# Contributing to Wavu

Thank you! Wavu is kept deliberately small: few moving parts, no compiled
Java, and the standard library where reasonable. Please keep it that way. See
[docs/decisions.md](docs/decisions.md) before proposing a new dependency or
layer.

## Setup

```
git clone https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu
cd Wavu
pixi run test
```

See [docs/development.md](docs/development.md) for the integration and Fiji
tests.

## Commits: Conventional Commits

The commit messages drive the version number and the changelog
([release-please](https://github.com/googleapis/release-please)):

| prefix | effect |
|---|---|
| `feat: ...` | new feature → minor bump (patch while < 1.0) |
| `fix: ...` | bug fix → patch bump |
| `feat!: ...` / `BREAKING CHANGE:` in the body | major bump (minor while < 1.0) |
| `docs:`, `test:`, `ci:`, `chore:`, `refactor:` | no release on their own |

Write tests first for anything that changes the worker protocol. The Groovy
client is covered by the Fiji smoke test (`tests/fiji/smoke_test.groovy`).
Extend it when you change `wavu_lib.groovy.txt`.

## How releases work

1. Merging to `main` makes release-please open or update a **release PR**,
   which bumps the version and updates `CHANGELOG.md`.
2. Merging that PR tags `vX.Y.Z` and creates the GitHub Release. In the same
   workflow run, `release.yml` then:
   - builds the wheel and sdist, with the version taken from the tag
     (hatch-vcs),
   - builds `wavu-fiji-X.Y.Z.zip` (the Fiji scripts with the version filled
     in),
   - pushes `ghcr.io/oxford-zeiss-centre-of-excellence/wavu-worker:X.Y.Z` and
     `:latest`,
   - attaches pixi-pack offline bundles for linux-64, osx-64, osx-arm64 and
     win-64,
   - uploads to the Fiji update site "Wavu", only if the repository variable
     `FIJI_UPDATE_SITE` is `true` and the secrets exist,
   - publishes to PyPI, only if the variable `PYPI_PUBLISH` is `true`
     (trusted publishing).
3. Every week, `weekly.yml` tests against the newest Fiji, runs the cellpose
   example, and refreshes `pixi.lock` files. It merges the update only after
   the tests pass on the new locks.

Nobody edits version numbers by hand.
