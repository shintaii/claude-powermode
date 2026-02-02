# Anti-Slop Guardrails

"Slop" is over-engineered, unnecessarily complex code that looks impressive but adds no value. This guide helps you avoid it.

## Core Principle

> "What's the simplest thing that could work?"

Before creating new tasks, methods, or complex architectures, ask:
- Can this be solved with a simple loop or conditional?
- Am I building for a real need or a hypothetical future?
- Is this complexity justified by the problem?

---

## Hard Blocks (NEVER violate)

### Type Safety Violations

| Violation | Why It's Banned |
|-----------|-----------------|
| `as any` | Defeats TypeScript's purpose |
| `@ts-ignore` | Hides real errors |
| `@ts-expect-error` | Same as above |
| `// eslint-disable` (without reason) | Hides real issues |

**Instead:** Fix the actual type error. If it's genuinely complex, add a comment explaining why and use a more specific type.

### Error Handling Violations

| Violation | Why It's Banned |
|-----------|-----------------|
| `catch(e) {}` | Silently swallows errors |
| `catch(e) { console.log(e) }` | Logs but doesn't handle |
| Catching and re-throwing without adding context | Pointless |

**Instead:** Handle errors meaningfully or let them propagate.

### Testing Violations

| Violation | Why It's Banned |
|-----------|-----------------|
| Deleting failing tests | Tests protect behavior |
| Skipping tests to pass CI | Same as above |
| Mocking everything | Tests nothing real |

**Instead:** Fix the code to make tests pass, or update tests if requirements changed (with explanation).

### Debugging Violations

| Violation | Why It's Banned |
|-----------|-----------------|
| Shotgun debugging | Random changes hoping something works |
| "Try this and see" | Not systematic |
| Adding more code without understanding | Makes it worse |

**Instead:** Understand the problem first. Add logging to trace the issue. Fix the root cause.

---

## Soft Guidelines (Prefer to Follow)

### Keep Solutions Localized

**Bad:** Problem in one method → changes across 5 files
**Good:** Problem in one method → fix in that method

If a fix requires touching many files, pause and ask: Is this really necessary?

### Minimal Changes for Bug Fixes

**Rule:** Fix minimally. NEVER refactor while fixing.

**Bad:**
```
// Fixing a null check, but also:
// - Renamed variables
// - Extracted a method
// - Changed formatting
// - "Improved" adjacent code
```

**Good:**
```
// Added null check on line 42
if (user != null) {
  // existing code
}
```

### Avoid Premature Abstraction

**Signs of premature abstraction:**
- "We might need this later"
- "For flexibility"
- "In case we want to..."
- One implementation of an interface

**Rule:** Abstract when you have 3+ concrete cases, not before.

### Prefer Existing Libraries

**Bad:** Writing a new date formatter when `date-fns` is already in package.json
**Good:** Using the library that's already there

**Exception:** If the library is deprecated, insecure, or genuinely doesn't fit.

---

## Common Slop Patterns

### The Architecture Astronaut

**Slop:**
```
// For a simple CRUD operation:
AbstractFactory → FactoryFactoryImpl → ConcreteFactory → 
Builder → Director → Product → ProductDTO → ProductMapper → ...
```

**Clean:**
```
function createUser(data) {
  return db.users.create(data)
}
```

### The Future-Proofer

**Slop:**
```
// "We might need multiple database types"
interface DatabaseAdapter { ... }
class PostgresAdapter implements DatabaseAdapter { ... }
class MySQLAdapter implements DatabaseAdapter { ... }  // never used
class MongoAdapter implements DatabaseAdapter { ... }  // never used
```

**Clean:**
```
// We use Postgres
const db = new PostgresClient()
```

### The Config Everything

**Slop:**
```
// 50-line config file for:
const config = {
  featureFlags: { enableButton: true },
  ui: { buttonColor: 'blue', buttonText: 'Submit' },
  ...
}
```

**Clean:**
```
<button class="blue">Submit</button>
```

### The Wrapper Wrapper

**Slop:**
```
// Wrapping a library that doesn't need wrapping
class HttpClient {
  constructor() { this.axios = axios }
  get(url) { return this.axios.get(url) }
  post(url, data) { return this.axios.post(url, data) }
}
```

**Clean:**
```
import axios from 'axios'
// Just use axios directly
```

---

## Self-Check Questions

Before submitting code, ask:

1. **Is this the simplest solution?**
   - Could a junior developer understand it?
   - Is every line necessary?

2. **Am I solving a real problem?**
   - Is this a current need or hypothetical future?
   - Would deleting this break something today?

3. **Did I change only what's necessary?**
   - Bug fix = minimal change
   - Feature = scoped to feature
   - No drive-by refactoring

4. **Is the complexity justified?**
   - Does the problem warrant this solution?
   - Would I be embarrassed explaining this to a colleague?

---

## The 20-Line Test

> "Sometimes a 20-line change is better than a 200-line architectural shift."

If you're about to make a large change, stop and ask:
- Is there a smaller change that achieves the same goal?
- Am I solving the actual problem or a generalized version?
- Would a simple loop or conditional work instead?
