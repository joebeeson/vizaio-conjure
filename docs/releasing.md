# Releasing

## Registry setup

Configure two Trusted Publishers, one on TestPyPI and one on PyPI:

- repository: `joebeeson/vizaio-conjure`
- workflow: `.github/workflows/publish.yml`
- environment: `testpypi` or `pypi`

The workflow uses OIDC and never accepts a package-upload token.

## Release flow

1. Update `version` in `pyproject.toml` and run `uv lock`.
2. Run `just check`, `just prek`, `uv build`, and `uv run --with twine twine check dist/*` locally.
3. Commit the version change and push a matching annotated tag, such as `v0.1.0rc1`.
4. The tag workflow runs tests, builds the wheel and source archive, and creates
   or updates the GitHub release.
5. Dispatch **Publish Python package** on that tag with `testpypi`.
6. Install from TestPyPI in a clean environment using PyPI as the dependency
   index, then run the CLI dry-run and profile tests.
7. Promote by changing the version to `0.1.0`, pushing `v0.1.0`, and dispatching
   the workflow with `pypi`.

Do not put PyPI API tokens in repository secrets; the workflow uses OIDC
Trusted Publishing for both registries.
