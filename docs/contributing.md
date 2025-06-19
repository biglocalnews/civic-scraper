```{highlight} shell
```

(contributing)=

# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at <https://github.com/biglocalnews/civic-scraper/issues>.

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Submit Feedback

The best way to send feedback is to file an issue at <https://github.com/biglocalnews/civic-scraper/issues>.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

### Do Research

This project involves a fair bit of research, especially with respect to locating
platforms and sites to scrape. Research jobs are great ways to get involved if
you don't write code but still want to pitch in. Anything tagged
with the "research" and "help wanted" labels on GitHub is fair game.

### Write Documentation

civic-scraper could always use more documentation, whether as part of the
official civic-scraper docs, in docstrings, or even on the web in blog posts,
articles, and such.

Our [official docs] use reStructuredText and Sphinx. To contribute documentation without completing the full repo setup (only required for code logic):

1. Fork and clone this repo
2. Create a simple virtual environment: `python3 -m venv civic-scraper-env` 
3. Activate your new virtual env: `source civic-scraper-env/bin/activate`
4. Install requirements for documentation: `pip install -r docs/requirements.txt`
5. Create a branch for your doc updates and start writing!
   - Use `make serve-docs` command to run a Sphinx server locally that displays doc pages and allows auto reloading of pages in browser when changes are made to a file.
6. Create a GitHub Pull Request once you're ready to send us your changes

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it. Follow the Get Started instructions below to get your local environment setup.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it. Follow the Get Started instructions below to get your local environment setup.

## Get Started!

Ready to contribute a bug fix or feature? Here's how to set up `civic-scraper` for local development. 

Note: While there are many ways to setup a virtual environment in Python, we recommend using Pipenv in order to keep your setup aligned with the continuous deployment configuration.

### Fork and clone the `civic-scraper` repo 

1. Fork the `civic-scraper` repo on GitHub.

2. Clone your fork locally:

   ```
   $ git clone git@github.com:your_name_here/civic-scraper.git
   ```

### Prep your development environment 

3. Make sure you have Python 3.9 installed: 
    - You can check this by running:

    ```bash
    python3 --version
    ```

4. Install `pipenv` (if you don't have it already):

   ```bash
   pip install pipenv
   ```

   Or, if you use Homebrew (recommended):

   ```bash
   brew install pipx
   pipx install pipenv
   ```

### Create your virtual environment & install dependencies

5. In the root of the project directory, run

   ```bash
   pipenv install --dev
   ```

💡 Pro Tips

- If you ever get weird errors when setting up your virtual environment, try removing and recreating it: 

   ```bash
   pipenv --rm
   pipenv install --dev
   ```
- To install a new package:

   ```bash
   pipenv install package-name
   ```

   - Add `--dev` to the above if the new package is just for development (like pytest)

## Making changes 

6. Create a branch for local development on your fork:

   ```
   $ git checkout -b name-of-your-bugfix-or-feature
   ```

7. Make your changes and be sure to add/update tests!

### Check your changes

When you're done making changes, you'll want to check that your changes pass linting requirements (using flake8) and the tests, including testing other Python versions (using tox).

7. Run style checks on everything in `civic_scraper/` and `tests/`: 
   
   ```bash
   pipenv run flake8 civic_scraper tests
   ```

8. Run tests: 

   ```bash
   pipenv run pytest
   ```

9. Check formatting using

   ```bash
   pipenv run flake8
   ```

10. Commit your changes and push your branch to GitHub:

   ```
   $ git add .
   $ git commit -m "Your detailed description of your changes."
   $ git push origin name-of-your-bugfix-or-feature
   ```

11. Submit a pull request through the GitHub website.


## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, please be sure to review the docs
   and include necessary updates. For example, new classes, methods
   and functions should be documented.
3. The pull request should work for Python version 3.9 or higher. Check
   <https://travis-ci.com/github/biglocalnews/civic-scraper/pull_requests>
   and make sure that the tests pass for all supported Python versions.

[official docs]: https://civic-scraper.readthedocs.io/en/latest/?badge=latest
