
Steps to do a new release
---------------------------

- Open a shell at the proper place (something as `X:\robocorpws\robotframework-lsp\robotframework-ls`)

- Create release branch (`git branch -D release-robotframework-lsp&git checkout -b release-robotframework-lsp`)

- Update version (`python -m dev set-version 1.15.0`).

- Update README.md to add notes on features/fixes (on `robotframework-ls` and `robotframework-intellij`).

- Update changelog.md to add notes on features/fixes and set release date (on `robotframework-ls` and `robotframework-intellij`).

- Update build.gradle version and patchPluginXml.changeNotes with the latest changelog (html expected).
  - Use `https://markdowntohtml.com/` to convert the changelog to HTML.

- Push contents, get the build in https://github.com/robocorp/robotframework-lsp/actions and install locally to test.
  - `mu acp Robot Framework Language Server Release 1.15.0`

- Rebase with master (`git checkout master&git rebase release-robotframework-lsp`).

- Create a tag (`git tag robotframework-lsp-1.15.0`) and push it.

- Send release msg. i.e.:

Hi @channel,

I'm happy to announce the release of `Robot Framework Language Server 1.15.0`.

### New features

- Completion suggestions now recognize Robot Framework 7.4 typed variables, including the new `Secret` type and other builtin converters.
- Language server features that rely on Robot Framework 7.4 are gated to only activate when the detected runtime supports them.
- Linting now warns when typed `Secret` variables are initialized with literal values, matching Robot Framework 7.4 semantics.
- Attribute completions offer `.value` for typed `Secret` variables to quickly access the underlying secret value.


### Bugfixes

- Guarded 7.4-specific completions to avoid offering unsupported types on earlier Robot Framework versions.

### Intellij

- Marked as compatible with the latest version of Intellij/ PyCharm.

Official clients supported: `VSCode` and `Intellij`.
Other editors supporting language servers can get it with: `pip install robotframework-lsp`.

Install `Robot Framework Language Server` from the respective marketplace or from one of the links below.
Links: [VSCode](https://marketplace.visualstudio.com/items?itemName=robocorp.robotframework-lsp), [Intellij](https://plugins.jetbrains.com/plugin/16086-robot-framework-language-server/versions/stable/) , [OpenVSX](https://open-vsx.org/extension/robocorp/robotframework-lsp), [PyPI](https://pypi.org/project/robotframework-lsp/), [GitHub (sources)](https://github.com/robocorp/robotframework-lsp/tree/master/robotframework-ls)
