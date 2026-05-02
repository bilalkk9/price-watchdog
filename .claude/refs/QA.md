# QA Checklist (run mentally before marking any file done)

## Before writing
- [ ] Read existing interfaces it will depend on
- [ ] Check SECURITY.md rules apply to this module

## While writing
- [ ] Type hints on every function signature
- [ ] One-line docstring on every public function
- [ ] All external input validated at entry point
- [ ] All DB queries parameterized
- [ ] Errors caught specifically (not bare `except Exception`)
- [ ] No secrets in any string literal

## After writing
- [ ] Tests cover: happy path, empty/None input, network/API failure, invalid types
- [ ] `python -m py_compile <file>` passes
- [ ] `python -m pytest tests/ -q` passes
- [ ] No TODO/FIXME left that aren't tracked

## Test file convention
`tests/test_<module>.py` — mirror the module name
Use real assertions, not just `assert result is not None`
