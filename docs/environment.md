# Development Environment

Use a clean checkout and the runtime version declared by the project. Install
dependencies using [INSTALL.md](../INSTALL.md), then run the checks listed in
[CONTRIBUTING.md](../CONTRIBUTING.md) and CI.

Keep credentials, host data, and production exports outside the source tree.
Validate distribution-specific behavior on separate supported Linux systems;
synthetic fixtures do not establish host-level kernel or security-module behavior.
