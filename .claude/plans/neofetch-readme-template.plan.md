# Plan: Image → ASCII Pipeline (M2)

**Source PRD**: `.claude/prds/neofetch-readme-template.prd.md`  
**Selected Milestone**: M2 — Image → ASCII pipeline  
**Complexity**: Medium

## Summary

Allow users to drop a `portrait.png` or `portrait.jpg` in the repo root; the build system automatically converts it to ASCII art and embeds it in both SVGs. No manual ASCII editing. Graceful fallback to placeholder if image is missing or conversion fails.

## Key Design Decisions

1. **Auto-detect image files** (not config field) — simpler UX. User drops file → runs `python build.py` → done. Config can add custom path in M4 if needed.
2. **Image requirements** — document: high contrast, simple subject, square crop. Ship a known-good test image to confirm pipeline works.
3. **Library choice** — TBD via spike. Candidates: `ascii-magic`, `image-to-ascii`, or Pillow + custom. Test on real portrait.

## Patterns to Mirror

| Category | Source | Pattern |
|---|---|---|
| Naming | `build.py:19-22` | Module-level path constants; functions snake_case; files kebab-case |
| Error handling | `build.py:64-71` | sys.exit(1) + stderr message for file/parse errors; graceful fallback for missing files |
| Logging | `build.py:277` | Simple print() to stdout on success |
| Data access | `build.py:75-82` | Graceful file loading with placeholder fallback |
| Tests | `test_build.py` | pytest + monkeypatch; test names: `test_{function}_{scenario}` |

## Files to Change

| File | Action | Why |
|---|---|---|
| `image_to_ascii.py` | CREATE | New module: load image → convert to ASCII lines |
| `build.py` | UPDATE | Auto-detect portrait.png/jpg; load via image_to_ascii if present, else fall back to ascii-art.txt |
| `test_build.py` | UPDATE | Test image loading, conversion fallback, and placeholder behavior |
| `requirements.txt` | UPDATE | Add chosen ASCII library |
| `config.yml` | No change | Portrait detection is automatic; config stays simple |
| `README.md` | UPDATE | Document portrait.png/jpg drop + conversion; image requirements |
| `ascii-art.txt` | No change | Remains fallback; ASCII pipeline supersedes it if image present |

## Tasks

### Task 1: Library Spike (1–2 hours)
- **Action**: Test 2–3 ASCII conversion libraries on a sample portrait (e.g., a test photo of yourself or a well-lit portrait).
  - Candidates: `image-to-ascii`, `ascii-magic`, Pillow + custom grayscale+threshold
  - Output metric: Best visual quality + maintainability
- **Mirror**: Treat like investigation, not implementation. Document findings in `.claude/spikes/ascii-library-choice.md` with side-by-side outputs.
- **Validate**: `python spike_test.py portrait.jpg` produces ASCII preview; pick winner.

### Task 2: Implement `image_to_ascii.py` (1–1.5 hours)
- **Action**: Create new module with functions:
  - `detect_portrait() -> Optional[Path]` — look for `portrait.png` or `portrait.jpg` in repo root
  - `convert_portrait(path: Path, width: int = 50) -> list[str]` — load image, convert to ASCII lines, return list
  - `convert_with_fallback(portrait_path: Optional[Path], fallback_ascii_path: Path) -> list[str]` — use portrait if present, else load fallback
- **Mirror**: Follow `build.py` error-handling pattern: graceful fallback, clear error messages to stderr
- **Validate**: Unit tests pass for all three functions (see Task 3)

### Task 3: Update `test_build.py` (0.5–1 hour)
- **Action**: Add 7 new tests:
  - `test_detect_portrait_finds_png` — portrait.png in repo root
  - `test_detect_portrait_finds_jpg` — portrait.jpg in repo root
  - `test_detect_portrait_missing_returns_none` — no portrait file
  - `test_convert_portrait_returns_list_of_strings` — conversion succeeds
  - `test_convert_portrait_file_missing_raises` — missing file error
  - `test_convert_with_fallback_uses_portrait_if_present` — portrait overrides fallback
  - `test_convert_with_fallback_uses_fallback_if_no_portrait` — fallback on missing image
- **Mirror**: Follow `test_build.py` style (fixtures, monkeypatch, descriptive names)
- **Validate**: `pytest test_build.py -v` — all tests pass, 80%+ coverage

### Task 4: Integrate into `build.py` (1 hour)
- **Action**: Update `main()` to:
  - Call `image_to_ascii.detect_portrait()` 
  - If portrait found, use `image_to_ascii.convert_with_fallback()`
  - Else fall back to `load_ascii()` (existing behavior)
  - Pass ASCII lines to `render_svg()` (unchanged)
- **Mirror**: Minimal changes to existing code; new logic goes into `image_to_ascii.py`
- **Validate**: `python build.py` produces SVGs with portrait if portrait.png present; reverts to ascii-art.txt if not

### Task 5: Update `requirements.txt` (0.25 hour)
- **Action**: Add chosen library (e.g., `image-to-ascii>=1.x.y` or equivalent)
- **Mirror**: Follow existing format: library name + version constraint
- **Validate**: `pip install -r requirements.txt` succeeds

### Task 6: Update README (0.5 hour)
- **Action**: Add section:
  - "Drop a portrait image"
  - Supported formats: PNG, JPG
  - Recommended: high-contrast, simple subject, square crop (or tool auto-crops?)
  - Example: "Just drop `portrait.png` in the repo root and re-run `python build.py`"
  - Fallback: "No portrait? ASCII art defaults to `ascii-art.txt`"
  - Test: "Run `python -m pytest test_build.py -v` to verify"
- **Mirror**: Clear, beginner-friendly; match existing README tone
- **Validate**: README mentions portrait before/after or animated GIF showing the feature

## Validation

```bash
# Spike: test library choice
python spike_test.py /path/to/sample/portrait.jpg

# Unit tests
pytest test_build.py -v --cov=image_to_ascii --cov=build --cov-fail-under=80

# Integration: portrait present
cp test-portrait.png portrait.png
python build.py
# Verify: light_mode.svg + dark_mode.svg contain portrait ASCII

# Integration: portrait absent
rm portrait.png
python build.py
# Verify: light_mode.svg + dark_mode.svg use ascii-art.txt

# End-to-end: fresh clone experience
git clone <template-repo> /tmp/test-clone
cd /tmp/test-clone
cp /path/to/test-portrait.png portrait.png
python build.py
# Verify: SVGs render with ASCII portrait
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| ASCII converter produces poor output for arbitrary photos | HIGH | Spike tests library on real portraits; document image requirements (high contrast, simple subject, square); ship test image in repo for validation |
| Library maintenance / deprecation | MEDIUM | Choose library with active maintainers + PyPI downloads; pin version; if deprecated, pivot to Pillow + custom |
| Slow conversion on large images | MEDIUM | Resize image before conversion; document performance expectations; add caching if needed in M3 |
| Portrait file not found → confusing error | LOW | Graceful fallback to ascii-art.txt; print message: "No portrait.png found; using ascii-art.txt" |

## Acceptance

- [ ] Library spike complete; choice documented
- [ ] `image_to_ascii.py` module created with 3 core functions
- [ ] `test_build.py` updated with 7 new tests, all passing
- [ ] `build.py` integrated to auto-detect + convert portrait
- [ ] `requirements.txt` updated with chosen library
- [ ] `README.md` updated with portrait instructions
- [ ] End-to-end validation: portrait present → ASCII embedded; portrait absent → fallback to ascii-art.txt
- [ ] Test coverage ≥ 80%
