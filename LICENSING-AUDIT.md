# Licensing and Contributor Audit

Audit date: 2026-07-12

## Scope

This audit reviewed the local Git repository history and current contributor documentation before moving from the previous placeholder/MIT-oriented licensing posture to a dual-license structure.

## Evidence Reviewed

- `git log` reported no prior commits in the local repository before the publication-candidate commit.
- `git status` showed the repository contents as uncommitted local files.
- Contributor documentation identifies Richard M. Infantado as primary author and specification editor.
- Robert Leroux (rl.isapience@gmail.com) is confirmed as a Contributor. He is not listed as a formal Internet-Draft author or editor in the front matter.

## Result

At the time the dual-license structure was adopted, the local pre-publication history contained no third-party commits known to the editor. Based on repository evidence, the project applies:

- CC BY 4.0 to specification text and documentation.
- Apache-2.0 to technical repository artifacts.

This is a repository-evidence statement, not a legal opinion. If additional pre-publication contributor history is discovered, the licensing basis should be revisited before publication.

Robert Leroux is acknowledged as a contributor. The repository does not currently contain evidence establishing whether Robert Leroux contributed copyrightable text outside Git or the license terms applicable to any such text. Formal publication should confirm that status; until then, no specific authored passage is attributed to him.

## Attribution Preservation

Contributor recognition is preserved in `CONTRIBUTORS.md`, `README.md`, and the Internet-Draft acknowledgements section.
