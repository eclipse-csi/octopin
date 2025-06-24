<h1 align="center">

<a href="https://octopin.readthedocs.org">
  <img style="width: 150px;" src="https://raw.githubusercontent.com/eclipse-csi/.github/refs/heads/main/artwork/eclipse-csi/logo-emblem/500x500%20Transparent.png">
</a>

</h1>

<p align="center">
  <a href="https://pypi.org/project/octopin"><img alt="PyPI" src="https://img.shields.io/pypi/v/octopin.svg?color=blue&maxAge=600" /></a>
  <a href="https://pypi.org/project/octopin"><img alt="PyPI - Python Versions" src="https://img.shields.io/pypi/pyversions/octopin.svg?maxAge=600" /></a>
  <a href="https://github.com/eclipse-csi/octopin/blob/main/LICENSE"><img alt="EPLv2 License" src="https://img.shields.io/github/license/eclipse-csi/octopin" /></a>
  <a href="https://github.com/eclipse-csi/octopin/actions/workflows/build.yml?query=branch%3Amain"><img alt="Build Status on GitHub" src="https://github.com/eclipse-csi/octopin/actions/workflows/build.yml/badge.svg?branch:main&workflow:Build" /></a>
  <a href="https://octopin.readthedocs.io"><img alt="Documentation Status" src="https://readthedocs.org/projects/octopin/badge/?version=latest" /></a><br>
  <a href="https://scorecard.dev/viewer/?uri=github.com/eclipse-csi/octopin"><img alt="OpenSSF Scorecard" src="https://api.securityscorecards.dev/projects/github.com/eclipse-csi/octopin/badge" /></a>
  <a href="https://slsa.dev"><img alt="OpenSSF SLSA Level 3" src="https://slsa.dev/images/gh-badge-level3.svg" /></a>
</p>

# Eclipse Octopin

Analyses and pins GitHub actions in your workflows.

This tool pins your GitHub Action versions to use the SHA-1 hash
instead of tag to improve security as Git tags are not immutable.

Converts `uses: aws-actions/configure-aws-credentials@v1.7.0` to
`uses: aws-actions/configure-aws-credentials@67fbcbb121271f7775d2e7715933280b06314838 # v1.7.0`

## Skipping actions

To skip a specific action from being pinned, you can add a comment `pinning: ignore`.

Example using the generic SLSA generator action which *MUST* be [referenced](https://github.com/slsa-framework/slsa-github-generator?tab=readme-ov-file#referencing-slsa-builders-and-generators) by a tag rather than a commit hash:

```yaml
provenance:
    needs: ['prepare', 'build-dist']
    permissions:
      actions: read
      contents: write
      id-token: write # Needed to access the workflow's OIDC identity.
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0 # pinning: ignore
    with:
      base64-subjects: "${{ needs.build-dist.outputs.hashes }}"
      upload-assets: true
```

## pre-commit hook

This repo provides a pre-commit hook to run `octopin pin`. Add the following
snippet to your `.pre-commit-config.yaml` to use.

```yaml
- repo: https://github.com/eclipse-csi/octopin
  rev: main  # Recommended to pin to a tagged released
  hooks:
  - id: pin-versions
```
