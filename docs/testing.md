# Testing

Testing gazer has two surfaces: the browser-rendered animation (visual, subjective) and the behavioral logic (compositor, drive system, state machine — pure JS that can be tested without a browser). This doc covers both, plus the WebSocket integration layer between them.

---

## Manual testing

The fastest way to verify everything is working. Open `index.html` in a browser and work through each area.

### Compositor & behaviors

1. Open the **Compositor** accordion → **GAZE** tab
2. Click each of the 15 behavior buttons — verify:
   - Active button highlights (teal)
   - Status bar updates (G: STATE)
   - Transition progress bar fills and fades
   - Eye movement changes character (speed, radius, pause rhythm)
3. Switch to **EXPRESSION** tab — repeat for all 15
4. Set GAZE and EXPRESSION to different states (e.g. `attentive` + `pleased`) — verify both layers are independent
5. Set a state with a slow enter (e.g. `resting` at 1.5s) — watch the blend bar fill slowly
6. Trigger `interrupted` — should snap instantly and auto-return after 0.5s (bar drains orange)

### Transition blending

- `resting → alert`: verify the 0.25s override (faster than resting's default exit)
- `pleased → uncomfortable`: verify the 0.90s reluctant drag
- `uncomfortable → pleased`: verify 0.55s cautious brightening

### Micro-expressions

In the **EXPRESSION** panel, scroll to the MICRO-EXPRESSIONS section:
1. Set a base affect state (e.g. `idle`)
2. Click each preset — Startle, Wince, Brighten, Doubt, Drift
3. Verify:
   - Face changes briefly (fast snap in)
   - Progress bar turns gold and drains
   - Returns to previous affect automatically
4. Click a full affect button mid-micro — verify the micro is cancelled, full state takes over

### Drive system

1. Open the **Drive** accordion
2. Click **DRIVE ON** — button turns teal
3. Watch the pressure bars — `idle` and `curious` should build; active state bars brighten
4. Wait 30–60 seconds — verify the robot shifts between `idle` and `curious` autonomously
5. Test **GAZE PINNED** — toggles gaze layer lockout; drive should still move expression
6. Test **EXPR PINNED** — expression stays fixed, gaze moves autonomously
7. Adjust **Novelty decay** slider up — robot should become more restless (switches more often)
8. Adjust **Hysteresis** slider up — robot should become more sticky (switches less)

### Transition enforcer

With drive ON:
1. Manually set state to `resting`
2. Let drive run — it should move to `waking` first, then `idle`, never jumping directly to other states
3. Inject `curious` pressure via WebSocket: `python3 send.py raw '{"type":"pressure","state":"curious","amount":0.8}'`
4. Verify the robot wakes before becoming curious

### Principles off switch

1. Click **PRINCIPLES ON** at the top of the right panel — button turns red, label changes to **PRINCIPLES OFF**
2. Verify immediately:
   - Saccades move in straight lines (no arc)
   - No wind-up before saccades (anticipation)
   - No overshoot/settle on landing
   - Eye shape doesn't deform during fast saccades
   - Head moves to target without overshoot
3. Click again — verify all behaviors restore to saved values

### 3D body & spring physics

1. Drag the yellow ball — head tracks it with overshoot and arc tilt
2. Release — body returns to idle wander with spring overshoot
3. With principles OFF — drag ball and verify no overshoot, no arc tilt
4. Adjust **Head arc tilt** slider — verify head tilts into turns more or less

### Visual overlays

In the **Gaze** and **Visual** panels:
- Toggle arc trail — colored path should appear behind pupil
- Toggle saccade target indicator — marker appears ahead of each saccade
- Toggle planning grid — crosshair and border zone appear
- Toggle pupils/lids/brows/mouth visibility checkboxes

---

## WebSocket testing

`server.py` is the relay; `send.py` sends one-shot commands. Start both before testing:

```bash
python3 server.py &
# open index.html in browser first
```

### Current send.py commands

```bash
python3 send.py behavior attentive
python3 send.py param gazeSpeed 2.0
python3 send.py params gazeSpeed=1.5 pupilSize=0.6
python3 send.py look 0.5 -0.2
python3 send.py blink
python3 send.py color eyeColor '#ff0000'
python3 send.py raw '<json>'
```

### Commands not yet in send.py (use `raw`)

```bash
# Compositor layers
python3 send.py raw '{"type":"attn","value":"alert"}'
python3 send.py raw '{"type":"affect","value":"pleased"}'

# Micro-expression
python3 send.py raw '{"type":"micro","value":"confused","hold":0.3}'

# Drive events
python3 send.py raw '{"type":"event","value":"face_detected","data":{"x":0.2,"y":0.1}}'
python3 send.py raw '{"type":"event","value":"startle"}'
python3 send.py raw '{"type":"event","value":"speech_start"}'
python3 send.py raw '{"type":"event","value":"speech_end"}'

# Direct pressure injection
python3 send.py raw '{"type":"pressure","state":"curious","amount":0.5}'
```

> `send.py` should be updated to support `attn`, `affect`, `micro`, `event`, and `pressure` commands natively. Currently they require the `raw` workaround.

### Sequence testing

Write multi-step sequences as Python scripts using the `websockets` library directly:

```python
# test_conversation.py
import asyncio, json, websockets

async def run():
    async with websockets.connect("ws://localhost:8765") as ws:
        async def send(msg):
            await ws.send(json.dumps(msg))
            await asyncio.sleep(0.1)

        await send({"type": "attn",   "value": "listening"})
        await send({"type": "affect", "value": "engaged"})
        await asyncio.sleep(3)
        await send({"type": "event",  "value": "speech_start"})
        await asyncio.sleep(2)
        await send({"type": "micro",  "value": "confused", "hold": 0.25})
        await asyncio.sleep(1)
        await send({"type": "event",  "value": "speech_end"})

asyncio.run(run())
```

---

## Automated testing

### 1. Logic unit tests (no browser required)

The compositor, drive system, state machine, and transition enforcer are pure JS — no DOM, no canvas. These can be extracted and tested with Node.js.

**Prerequisite:** engine extraction (see `docs/robot-architecture.md`). Until that's done, the functions can be copied into a test file or evaluated via Playwright's `page.evaluate()`.

**Test file structure:**

```
tests/
  unit/
    compositor.test.js     — getCompositor(), _resolveTransition()
    behaviors.test.js      — all 15 behaviors well-formed
    drive.test.js          — pressure dynamics, enforceTransition()
    transitions.test.js    — transTable, transEnforcer
  integration/
    websocket.test.js      — send commands, verify state
  browser/
    visual.test.js         — Playwright, screenshot comparisons
```

**Example unit tests (Node.js + any test runner):**

```javascript
// compositor.test.js
describe('_resolveTransition', () => {
  test('uses behavior enterDur by default', () => {
    const { dur } = _resolveTransition('idle', 'alert');
    expect(dur).toBe(0.06);
  });

  test('uses transTable override for pair', () => {
    const { dur } = _resolveTransition('pleased', 'uncomfortable');
    expect(dur).toBe(0.90);
  });

  test('falls back to transitionDur if no enterDur', () => {
    params.transitionDur = 0.3;
    // a behavior with no enterDur defined
    const { dur } = _resolveTransition('idle', 'hypothetical');
    expect(dur).toBe(0.3);
  });
});

// drive.test.js
describe('enforceTransition', () => {
  test('resting cannot jump directly to speaking', () => {
    expect(enforceTransition('resting', 'speaking')).toBe('waking');
  });

  test('resting can exit to interrupted', () => {
    expect(enforceTransition('resting', 'interrupted')).toBe('interrupted');
  });

  test('waking cannot jump to speaking', () => {
    expect(enforceTransition('waking', 'speaking')).toBe('idle');
  });

  test('idle has no restrictions', () => {
    expect(enforceTransition('idle', 'speaking')).toBe('speaking');
  });
});

// behaviors.test.js
describe('behaviors', () => {
  const required = ['gazeRadius', 'speedMult', 'blinkMult', 'lidOpenness', 'enterDur', 'enterEase'];

  Object.entries(behaviors).forEach(([name, beh]) => {
    test(`${name} has all required fields`, () => {
      required.forEach(field => {
        expect(beh[field]).toBeDefined();
      });
    });
  });

  test('all 15 behaviors present', () => {
    expect(Object.keys(behaviors)).toHaveLength(15);
  });

  test('interrupted has maxHold', () => {
    expect(behaviors.interrupted.maxHold).toBe(0.5);
  });
});
```

**Pressure dynamics test:**

```javascript
describe('updateDrive pressure', () => {
  beforeEach(() => {
    state.drive.pressure = {};
    state.drive.enabled = true;
    state.attn = 'idle';
    state.affect = 'idle';
  });

  test('idle pressure rises toward driveProfile target', () => {
    updateDrive(1.0); // 1 second
    expect(state.drive.pressure.idle).toBeGreaterThan(0);
    expect(state.drive.pressure.idle).toBeLessThanOrEqual(driveProfile.idle);
  });

  test('active state decays faster than inactive', () => {
    // Give both equal starting pressure
    state.drive.pressure.idle    = 0.3;
    state.drive.pressure.curious = 0.3;
    updateDrive(0.5);
    // idle is active — should have decayed more
    expect(state.drive.pressure.idle).toBeLessThan(state.drive.pressure.curious);
  });
});
```

### 2. Browser integration tests (Playwright)

Playwright can load `index.html`, drive the UI, and check JS state — useful for testing interactions between the rendering and logic layers.

**Setup:**
```bash
npm init -y
npm install --save-dev playwright
npx playwright install chromium
```

**Example test:**

```javascript
// tests/browser/compositor.test.js
const { test, expect } = require('@playwright/test');

test.beforeEach(async ({ page }) => {
  await page.goto('file:///path/to/gazer/index.html');
  await page.waitForLoadState('networkidle');
});

test('setAttn changes state.attn', async ({ page }) => {
  await page.evaluate(() => window.setAttn('alert'));
  const attn = await page.evaluate(() => window.state.attn);
  expect(attn).toBe('alert');
});

test('interrupted auto-returns after maxHold', async ({ page }) => {
  await page.evaluate(() => window.setAttn('idle'));
  await page.evaluate(() => window.setAttn('interrupted'));
  await page.waitForTimeout(800); // maxHold is 0.5s, allow buffer
  const attn = await page.evaluate(() => window.state.attn);
  expect(attn).toBe('idle');
});

test('microExpress returns to previous affect', async ({ page }) => {
  await page.evaluate(() => window.setAffect('idle'));
  await page.evaluate(() => window.microExpress('pleased', 0.3));
  const duringMicro = await page.evaluate(() => window.state.affect);
  expect(duringMicro).toBe('pleased');
  await page.waitForTimeout(500);
  const afterMicro = await page.evaluate(() => window.state.affect);
  expect(afterMicro).toBe('idle');
});

test('principles off zeroes arcCurvature', async ({ page }) => {
  const before = await page.evaluate(() => window.params.arcCurvature);
  await page.evaluate(() => window.togglePrinciples());
  const after = await page.evaluate(() => window.params.arcCurvature);
  expect(before).toBeGreaterThan(0);
  expect(after).toBe(0);
});

test('principles on restores arcCurvature', async ({ page }) => {
  const original = await page.evaluate(() => window.params.arcCurvature);
  await page.evaluate(() => window.togglePrinciples()); // off
  await page.evaluate(() => window.togglePrinciples()); // on
  const restored = await page.evaluate(() => window.params.arcCurvature);
  expect(restored).toBe(original);
});

test('enforceTransition blocks resting → speaking', async ({ page }) => {
  const result = await page.evaluate(() => window.enforceTransition('resting', 'speaking'));
  expect(result).toBe('waking');
});

test('drive pressure rises for idle', async ({ page }) => {
  await page.evaluate(() => {
    window.state.drive.enabled = true;
    window.state.drive.pressure = {};
    window.updateDrive(1.0);
  });
  const pressure = await page.evaluate(() => window.state.drive.pressure.idle);
  expect(pressure).toBeGreaterThan(0);
});
```

**Visual snapshot testing** (with Playwright):

```javascript
test('idle state visual baseline', async ({ page }) => {
  await page.evaluate(() => window.setAttn('idle'));
  await page.waitForTimeout(500);
  await expect(page.locator('canvas')).toHaveScreenshot('idle-baseline.png');
});
```

Screenshots are saved on first run and compared on subsequent runs. Useful for catching regressions in rendering.

### 3. WebSocket integration tests

```python
# tests/test_ws_commands.py
import asyncio, json, websockets, pytest

WS = "ws://localhost:8765"

async def send_and_wait(ws, msg, delay=0.2):
    await ws.send(json.dumps(msg))
    await asyncio.sleep(delay)

@pytest.mark.asyncio
async def test_behavior_command():
    async with websockets.connect(WS) as ws:
        await send_and_wait(ws, {"type": "behavior", "value": "attentive"})
        # No direct state read over WS yet — verify via Playwright in combined tests

@pytest.mark.asyncio
async def test_all_behaviors_accepted():
    behaviors = [
        'idle','attentive','curious','sleepy','alert','searching',
        'listening','processing','speaking','waiting','engaged',
        'confused','pleased','uncomfortable','waking','resting','interrupted'
    ]
    async with websockets.connect(WS) as ws:
        for name in behaviors:
            await send_and_wait(ws, {"type": "behavior", "value": name}, 0.05)
            # Should not throw or disconnect
```

---

## What to prioritize

| Area | Manual | Unit test | Browser test | WS test |
|------|--------|-----------|--------------|---------|
| Compositor blending | ✓ | high | medium | low |
| All 15 behaviors complete | ✓ | high | low | low |
| Transition enforcer | ✓ | high | medium | low |
| Drive pressure dynamics | ✓ | high | medium | low |
| Micro-expressions | ✓ | low | high | medium |
| Principles toggle | ✓ | medium | high | low |
| WebSocket commands | ✓ | n/a | low | high |
| Spring/arc physics | ✓ | n/a | high (snapshot) | n/a |

Logic-heavy areas (compositor, drive, enforcer) are most valuable as unit tests. Visual/timing-dependent areas (micro-expressions, principles, spring physics) are best verified with browser tests. WebSocket commands are best tested end-to-end with a live server.

---

## Next steps

1. **Update `send.py`** — add `attn`, `affect`, `micro`, `event`, `pressure` commands natively
2. **Extract engine** — move compositor + drive logic out of `index.html` into `engine.js` so unit tests don't require a browser
3. **Set up Playwright** — `npm init` + `playwright install`; write the browser tests above
4. **CI** — GitHub Actions workflow that starts a static server, runs Playwright tests, and runs Node.js unit tests on each push
