# Releasing

## Current state

The repository is private and the package is not published yet. The release
workflow is prepared for signed GitHub release artifacts. The publish workflow
is dormant until the PyPI and TestPyPI projects and Trusted Publishers are
configured.

## Release flow

1. Update `version` in `pyproject.toml` and run `uv lock`.
2. Run `just check` and `just prek` locally.
3. Commit the version change and push a tag such as `v0.1.0a2`.
4. The tag workflow runs tests, builds the wheel and source archive, and creates
   or updates the GitHub release.
5. After Trusted Publishing is configured and publication is approved for a
   later milestone, dispatch the PyPI workflow explicitly.

For a rehearsal, dispatch **Publish to Python Package Index** with `testpypi`.
Do not put PyPI API tokens in repository secrets; the workflow uses OIDC
Trusted Publishing.
