# Contribute to vgamepad

Thanks everyone for you interest in `vgamepad`, your contributions to the repo are greatly valued.

## Important guidelines for Pull Requests (PRs)

Many projects are using `vgamepad` as a dependency.
For their security and stability, it is important that each and every line of each pull request is thoroughly reviewed before being merged to the library.

I (Yann) am alone actively maintaining this library at the moment, and am quite busy with other projects...
So please stick to the following guidelines to make my life easier when submitting PRs:

- **Short, simple and clean**. Typically, a PR should change less that 10 lines if fixing a small concern, and less than 250 lines if introducing a major feature.
- **One concern per PR**. Please refrain from writing PRs that fix multiple concerns at once, as these are harder to merge. If fixing several issues, please open one clean PR per issue.
- **No LLM-generated code**. I know that LLMs are helpful teachers, but if you let them code for you they create large chunks of code that your do not entirely understand. These are much harder for me to review than it is for you to write, so please refrain entirely from doing this when contributing to `vgamepad`.
- **No linter/formatter**. Please refrain from making any line change that doesn't do anything functionally useful (except perhaps adding useful comments). If the current codebase formatting is a real concern for you, please open a discussion for this and/or submit a PR that _only_ handles formatting and _nothing else_, otherwise I will most likely have to reject your PR because of random formatting changes all over the place.
- **No breaking change on Windows**. The Windows API and installation pipeline with automatic installation of ViGemBus from `pip` are stable and must not be broken.
