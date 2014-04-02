# RustFixer

This is a small script to automate fixes on Rust code following the language's development.

A lot of fixes are basic search-and-replace fixes, and are already done semi-automatically on Rust's codebase.

This script takes a username and repository name, forks and clones the repository, applies fixes, commits, pushes and creates a pull request.

Right now, the account used for this is mine, and it is hardcoded. It requires an app token with permission for repositories. This token is stored in settings.ini
