<style>
.md-content .md-typeset h1 { display: none; }
</style>

<p align="center">
    <em>Octopin, pinning of GitHub actions made easy.</em>
</p>
<p align="center">
<a href="https://github.com/eclipse-csi/octopin/actions?query=workflow%3ABuild" target="_blank">
    <img src="https://github.com/eclipse-csi/octopin/workflows/Build/badge.svg" alt="Test">
</a>
<a href="https://github.com/eclipse-csi/octopin/actions?query=workflow%3APublish" target="_blank">
    <img src="https://github.com/eclipse-csi/octopin/workflows/Publish/badge.svg" alt="Publish">
</a>
<a href="https://pypi.org/project/octopin" target="_blank">
    <img src="https://img.shields.io/pypi/v/octopin?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
</p>

---

**Documentation**: <a href="https://octopin.readthedocs.org" target="_blank">https://octopin.readthedocs.org</a>

**Source Code**: <a href="https://github.com/eclipse-csi/octopin" target="_blank">https://github.com/eclipse-csi/octopin</a>

---

Octopin is a command line tool to analyse and pin actions referenced in GitHub workflows.

The key features are:

* Listing **transitive dependencies** of GitHub workflows.
* **Pinning of GitHub Actions** in GitHub workflows.

## Installation

```console
$ pipx install octopin
```

## Usage

```console
$ octopin --help
                                                                                                                                                                                                                   
 Usage: octopin [OPTIONS] COMMAND [ARGS]...                                                                                                                                                                        
                                                                                                                                                                                                                   
 OctoPIN - Tool to pin used actions and analyse transitive dependencies of 
 GitHub workflows / actions.                                                                                                             
 Read more in the docs: https://octopin.readthedocs.org/.                                                                                                                                                          
                                                                                                                                                                                                                   
╭─ Options ──────────────────────────────────────────────────────────────────╮
│ --version                     Show the version and exit.                   │
│ --install-completion          Install completion for the current shell.    │
│ --show-completion             Show completion for the current shell, ...   │
│ --help                        Show this message and exit.                  │
╰────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────╮
│ dependencies   Print transitive workflow dependencies.                     │
│ pin            Pin actions used in workflows.                              │
╰────────────────────────────────────────────────────────────────────────────╯
```

## License

This project is licensed under the terms of the Eclipse Public License 2.0.
