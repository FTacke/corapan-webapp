# Safety Contract

The sync-lane refactor keeps these safety properties explicit:

- Data, Media, and BlackLab remain separate lanes
- manifest migration remains in place
- aborted-run marker checks remain in place
- empty-source directory rsync with `--delete` is blocked
- implausible remote target paths are blocked in the shared rsync path
- `scp -O` fallback remains available
- BlackLab validation requires a real hits query before swap and after publish

This contract is intentionally conservative.
Do not remove a workaround just because a cleaner abstraction exists.