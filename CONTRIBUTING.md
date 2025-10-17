# Contributing to Hybrid IDS

Thank you for your interest in contributing to the Hybrid IDS project! This document provides guidelines and best practices for contributing.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)

---

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- **Be respectful:** Treat everyone with respect and kindness
- **Be collaborative:** Work together and help each other
- **Be inclusive:** Welcome diverse perspectives and experiences
- **Be professional:** Keep discussions focused and constructive

---

## Getting Started

### Prerequisites

Before contributing, make sure you have:

1. **Forked** the repository
2. **Cloned** your fork locally
3. Set up the **development environment** (see [README.md](README.md))
4. Read the **[Master Control Plan](MCP_MASTER_PLAN.md)** and **[Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)**

### Setting Up Your Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/hybrid-ids-mcp.git
cd hybrid-ids-mcp

# Add upstream remote
git remote add upstream https://github.com/original/hybrid-ids-mcp.git

# Run setup script
./scripts/setup.sh

# Verify setup
make test
```

---

## Development Workflow

### Branch Naming Convention

Use descriptive branch names following this pattern:

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

**Examples:**
- `feature/add-tls-decoder`
- `bugfix/fix-memory-leak-parser`
- `docs/update-api-reference`

### Workflow Steps

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following coding standards

3. **Write tests** for your changes

4. **Run tests** to ensure nothing breaks:
   ```bash
   # C++ tests
   cd build && ctest

   # Python tests
   pytest tests/
   ```

5. **Commit your changes** with clear messages:
   ```bash
   git add .
   git commit -m "Add: TLS protocol decoder with handshake analysis"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub

---

## Coding Standards

### C++ Code Style

#### Formatting
- **Indentation:** 4 spaces (no tabs)
- **Line length:** Max 100 characters
- **Braces:** Opening brace on same line (K&R style)

#### Naming Conventions
```cpp
// Classes: PascalCase
class PacketCapture { };

// Functions: camelCase
void capturePackets() { }

// Variables: snake_case
int packet_count = 0;

// Constants: UPPER_SNAKE_CASE
const int MAX_BUFFER_SIZE = 1024;

// Member variables: trailing underscore
class Example {
private:
    int buffer_size_;
};
```

#### Example
```cpp
class PacketParser {
public:
    PacketParser(int max_depth);

    ParsedPacket parse(const uint8_t* data, size_t length);

private:
    int max_depth_;
    std::vector<Protocol> protocols_;

    bool validatePacket(const uint8_t* data);
};
```

#### Best Practices
- Use **RAII** for resource management
- Prefer **smart pointers** over raw pointers
- Use **const** whenever possible
- Avoid **naked new/delete**
- Use **nullptr** instead of NULL
- Add **comments** for complex logic

### Python Code Style

#### Formatting
- Follow **PEP 8** style guide
- Use **black** for automatic formatting
- **Type hints** for function signatures

#### Example
```python
from typing import List, Optional

class FeatureExtractor:
    """Extract features from network packets."""

    def __init__(self, feature_names: List[str]) -> None:
        self.feature_names = feature_names
        self.scaler: Optional[StandardScaler] = None

    def extract(self, packet_data: dict) -> np.ndarray:
        """
        Extract features from packet data.

        Args:
            packet_data: Dictionary containing packet information

        Returns:
            Feature vector as numpy array
        """
        features = []
        for name in self.feature_names:
            features.append(packet_data.get(name, 0.0))
        return np.array(features)
```

#### Best Practices
- Use **type hints**
- Write **docstrings** (Google style)
- Use **f-strings** for formatting
- Prefer **list comprehensions** over loops (when readable)
- Use **pathlib** for file paths
- Handle **exceptions** explicitly

### Code Documentation

#### C++ Documentation (Doxygen)
```cpp
/**
 * @brief Captures packets from network interface
 *
 * This class provides high-performance packet capture using libpcap.
 * It supports BPF filters and promiscuous mode.
 *
 * @example
 * PacketCapture capture("eth0", "tcp port 80");
 * capture.start();
 */
class PacketCapture {
    /**
     * @brief Start packet capture
     * @throws std::runtime_error if interface cannot be opened
     */
    void start();
};
```

#### Python Documentation (Google Style)
```python
def train_model(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    """
    Train Random Forest classifier for attack detection.

    Args:
        X_train: Training features (n_samples, n_features)
        y_train: Training labels (n_samples,)

    Returns:
        Trained RandomForestClassifier model

    Raises:
        ValueError: If training data is empty

    Example:
        >>> X_train = np.random.rand(1000, 41)
        >>> y_train = np.random.randint(0, 2, 1000)
        >>> model = train_model(X_train, y_train)
    """
```

---

## Testing Guidelines

### Unit Tests

#### C++ Unit Tests (Google Test)
```cpp
#include <gtest/gtest.h>
#include "packet_parser.h"

TEST(PacketParserTest, ParseValidTcpPacket) {
    PacketParser parser;
    uint8_t data[] = { /* valid TCP packet */ };

    ParsedPacket result = parser.parse(data, sizeof(data));

    EXPECT_EQ(result.protocol, Protocol::TCP);
    EXPECT_EQ(result.src_port, 12345);
    EXPECT_EQ(result.dst_port, 80);
}

TEST(PacketParserTest, HandleMalformedPacket) {
    PacketParser parser;
    uint8_t data[] = { /* malformed packet */ };

    EXPECT_THROW(parser.parse(data, sizeof(data)), std::runtime_error);
}
```

#### Python Unit Tests (pytest)
```python
import pytest
from src.ai.preprocessing import FeaturePreprocessor

@pytest.fixture
def preprocessor():
    return FeaturePreprocessor(feature_names=['duration', 'packet_count'])

def test_extract_features(preprocessor):
    packet_data = {'duration': 5.0, 'packet_count': 100}
    features = preprocessor.extract(packet_data)

    assert len(features) == 2
    assert features[0] == 5.0
    assert features[1] == 100

def test_handle_missing_features(preprocessor):
    packet_data = {'duration': 5.0}  # missing packet_count
    features = preprocessor.extract(packet_data)

    assert features[1] == 0.0  # Should use default value
```

### Integration Tests

Create integration tests in `tests/integration/` to test component interactions:

```python
def test_nids_to_ai_pipeline():
    """Test end-to-end data flow from NIDS to AI engine."""
    # Start components
    nids = NIDSEngine(config='test_nids.yaml')
    ai_engine = AIEngine(config='test_ai.yaml')

    # Send test packet
    test_packet = create_test_packet()
    nids.process_packet(test_packet)

    # Verify AI engine receives data
    result = ai_engine.get_result(timeout=5)
    assert result is not None
    assert result['packet_id'] == test_packet.id
```

### Test Coverage

- Aim for **>80% code coverage**
- Run coverage analysis:
  ```bash
  # C++
  cmake .. -DENABLE_COVERAGE=ON
  make coverage

  # Python
  pytest --cov=src --cov-report=html
  ```

---

## Documentation

### Required Documentation for New Features

1. **Code comments** - Explain complex logic
2. **Docstrings/Doxygen** - Document all public APIs
3. **README updates** - Update main README if needed
4. **Architecture docs** - Update architecture docs for significant changes
5. **User guide** - Add usage examples

### Documentation Format

- Use **Markdown** for all documentation
- Include **code examples** where applicable
- Add **diagrams** for complex concepts (use ASCII art or Mermaid)

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up-to-date with main

### PR Template

Use this template when opening a PR:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe tests performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks** run (CI/CD)
2. **Code review** by maintainers
3. **Changes requested** (if needed)
4. **Approval** and **merge**

---

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. Observe error '...'

**Expected behavior**
What should happen

**Environment**
- OS: Ubuntu 22.04
- Version: 0.1.0
- Config: [attach config file]

**Logs**
```
[paste relevant logs]
```
```

### Feature Requests

```markdown
**Feature Description**
Clear description of proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How could this be implemented?

**Alternatives Considered**
Other approaches considered
```

---

## Areas for Contribution

Looking for ways to contribute? Here are some areas:

### High Priority
- 🔴 **NIDS Engine:** Packet capture and parsing
- 🔴 **ML Models:** Model training and optimization
- 🔴 **Testing:** Unit and integration tests

### Medium Priority
- 🟡 **Documentation:** User guides and tutorials
- 🟡 **Dashboard:** Web UI development
- 🟡 **Performance:** Optimization and benchmarking

### Low Priority
- 🟢 **Examples:** Sample configurations and use cases
- 🟢 **Tools:** Utility scripts and helpers
- 🟢 **Research:** New detection algorithms

---

## Questions?

- Open a **[Discussion](https://github.com/yourusername/hybrid-ids-mcp/discussions)**
- Join our **community chat** (coming soon)
- Email the maintainers

---

## Recognition

Contributors will be:
- Listed in **CONTRIBUTORS.md**
- Mentioned in **release notes**
- Credited in **research papers** (if applicable)

---

**Thank you for contributing to Hybrid IDS!**

Your contributions help make network security better for everyone.
