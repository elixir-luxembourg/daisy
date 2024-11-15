# Contribution

This guide outlines the process for contributing to this repository.

## GitHub Workflow

We follow a standard GitHub workflow for contributions:

1. Fork the repository [if needed]
2. Create a new branch
3. Make your changes
4. Submit a pull request

## Pull Requests

- All major contributions should be made through pull requests (PRs).
- Branch names should start with the issue number (e.g., `124-fancy-new-feature`).
- PRs can be opened as soon as the branch is created. Use draft PRs for work in progress.
- PR titles should include the issue number (e.g., "#98: Improve error handling").
- Include relevant implementation notes and any deviations from the original issue description in the PR description.
- If the changes impact the user interface, include screenshots in the PR description.
- Resolve any merge conflicts before requesting a review.

## Definition of "Done" (DoD)

Before marking a PR as ready for review, ensure:

- All issue requirements are implemented
- CI pipeline is passing
- Test coverage is maintained or improved
- Unit tests cover the new implementation (except for very minor changes)
- Documentation (including README) is updated if necessary
- New methods and classes have docstrings and type hints

## Code Review Process

- At least one approval from another team member is required before merging.
- Reviewers should check out the branch and test the feature, not just review the code.
- Use GitHub's review features for inline comments and general feedback.
- The PR author should address all comments and request re-review when ready.
- Reviewers should resolve comment threads once satisfied with the changes.
- After all threads are resolved and the PR is approved, it can be merged.

## After Merging

- Close the related issue once the PR is merged and the implementation has been verified in the test environment.
