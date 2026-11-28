# Dependency setup actually executed

R 4.3.3 and the required installed R packages were reused. R Arrow is absent; the existing `../iress-export/.venv/bin/python` supplies Python 3.12, PyArrow 26.0.1 and Pandas 3.1.1 for local I/O/contract checks. No statistical calculations were transferred to Python.

The original standalone verifier passed using that interpreter. No IRESS extraction, source changes or institutional-data upload occurred.

An attempted `install.packages("waldo", lib="mon_thesis/.Rlib", repos="https://cloud.r-project.org", dependencies=FALSE)` could not reach the repository. No package was installed; the empty local directory was removed. The system waldo 0.5.2/new glue namespace cycle was resolved by preloading glue in the test entry point. Unsetting LC_ALL in that process also avoids testthat language-restoration warnings, leaving the session's locale unchanged.

Initial renv snapshot failed because its default home cache was not writable. A retry with RENV_PATHS_ROOT=/tmp/part-a-renv and RENV_PATHS_CACHE=/tmp/part-a-renv/cache succeeded. renv.lock records actual installed package versions and recursive dependencies. A clean remote restore remains untested because network access is unavailable. See session_info.txt, source_contract.json and the root project README for reproducible commands.
