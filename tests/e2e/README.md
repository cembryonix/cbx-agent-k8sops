# E2E UI Tests

End-to-end browser tests using Playwright. Tests are defined in YAML for easy modification by non-developers.

## Quick Start

```bash
# Ensure app is running
reflex run

# Run tests (headless)
python tests/e2e/test_ui.py

# Run with visible browser
python tests/e2e/test_ui.py --visible

# Verbose output
python tests/e2e/test_ui.py -v
```

## Requirements

```bash
pip install playwright
playwright install chromium
```

## Test Structure

```
tests/e2e/
├── test_ui.py              # Test runner (Python)
├── test-cases/
│   └── ui-tests.yaml       # Test definitions (YAML)
└── README.md               # This file
```

## YAML Test Format

Tests are defined in `test-cases/ui-tests.yaml`:

```yaml
defaults:
  timeout: 30000  # Default timeout in ms

tests:
  - name: "test_name"           # Unique identifier
    description: "What it tests"
    action: "navigate|wait_for_text|check_element|interact"
    # ... action-specific fields
```

## Available Actions

### navigate

Load the app URL and check for errors.

```yaml
- name: "page_loads"
  action: "navigate"
  settings:
    wait_until: "networkidle"  # or "load", "domcontentloaded"
  expect:
    response_ok: true
    no_console_errors: true
```

### wait_for_text

Wait for specific text to appear on the page.

```yaml
- name: "initialization"
  action: "wait_for_text"
  settings:
    text: "Connected to K8S MCP server"
    timeout: 30000
  on_failure:
    check_selectors:
      - "[class*='error']"
```

### check_element

Check if any of the specified elements exist.

```yaml
- name: "sidebar_visible"
  action: "check_element"
  selectors:
    - "[data-testid='sidebar']"
    - "aside"
    - "[class*='sidebar']"
  soft_pass: true  # Don't fail if not found
  on_failure:
    screenshot: "/tmp/debug.png"
```

### interact

Execute a sequence of user interactions.

```yaml
- name: "send_message"
  action: "interact"
  steps:
    - type: "find_element"
      selectors:
        - "input[type='text']"
        - "textarea"
      required: true
    - type: "fill"
      value: "Hello!"
    - type: "press"
      key: "Enter"
    - type: "wait_for_response"
      timeout: 15000
      expect_any:
        - "response text"
        - "alternative"
  on_failure:
    screenshot: "/tmp/e2e_fail.png"
```

#### Interaction Step Types

| Type | Description | Fields |
|------|-------------|--------|
| `find_element` | Find element by selectors | `selectors`, `required` |
| `fill` | Type text into element | `value` |
| `press` | Press a key | `key` (e.g., "Enter", "Tab") |
| `wait_for_response` | Wait for text in body | `timeout`, `expect_any` |

## Adding New Tests

1. Edit `test-cases/ui-tests.yaml`
2. Add a new test entry:

```yaml
- name: "my_new_test"
  description: "Test something new"
  action: "check_element"
  selectors:
    - "[data-testid='my-element']"
```

3. Run tests to verify:

```bash
python tests/e2e/test_ui.py -v
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--url URL` | App URL (default: http://localhost:3000) |
| `--visible` | Show browser window |
| `-v, --verbose` | Verbose debug output |
| `--tests PATH` | Path to test YAML file |

## Best Practices

### Use data-testid Attributes

Prefer `data-testid` over CSS class selectors:

```yaml
# Fragile - breaks if CSS changes
selectors:
  - "[class*='sidebar']"

# Stable - explicit test hook
selectors:
  - "[data-testid='sidebar']"
```

Add to UI components:
```python
rx.box(..., data_testid="sidebar")
```

### Multiple Selector Fallbacks

Provide fallbacks for resilience:

```yaml
selectors:
  - "[data-testid='input']"      # Preferred
  - "input[type='text']"         # Fallback
  - "textarea"                   # Alternative
```

### Screenshot on Failure

Always capture screenshots for debugging:

```yaml
on_failure:
  screenshot: "/tmp/e2e_test_name.png"
```

### Soft Pass for Optional Elements

Use for elements that may not exist in all layouts:

```yaml
soft_pass: true  # Pass even if not found
```

## Debugging

### Run with visible browser

```bash
python tests/e2e/test_ui.py --visible -v
```

### Check screenshots

Failed tests save screenshots to paths specified in `on_failure.screenshot`.

### Common Issues

| Issue | Solution |
|-------|----------|
| "Playwright not installed" | `pip install playwright && playwright install chromium` |
| "Connection refused" | Ensure app is running: `reflex run` |
| Timeout errors | Increase timeout in YAML or use `--visible` to debug |
| Element not found | Check selectors, add `data-testid` to components |

## Current Tests

| Test | Description |
|------|-------------|
| `page_loads` | App loads without JS errors |
| `initialization` | Agent connects to MCP server |
| `sidebar_visible` | Sidebar/navigation is visible |
| `input_bar_visible` | Chat input is ready |
| `send_message` | Can send message and get response |

## Future Improvements

- [ ] Add `click` action for button interactions
- [ ] Add `select_option` for dropdowns
- [ ] Add settings panel tests (change provider/model)
- [ ] Add test isolation (fresh page per test)
- [ ] Add retry mechanism for flaky tests
- [ ] Add viewport testing (mobile/desktop)
- [ ] Generate HTML test report