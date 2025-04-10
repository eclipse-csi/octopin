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


## pre-commit hook

This repo provides a pre-commit hook to run `octopin pin`. Add the following
snippet to your `.pre-commit-config.yaml` to use.

```yaml
- repo: https://github.com/eclipse-csi/octopin
  rev: main  # Recommended to pin to a tagged released
  hooks:
  - id: pin-versions
```
