# RMAgent Documentation Index

Comprehensive documentation for RMAgent - AI-powered genealogy assistant for RootsMagic 11 databases.

## 📚 Documentation Overview

### For New Users

Start here if you're new to RMAgent:

1. **[README.md](../README.md)** - Project overview and quick start
2. **[INSTALL.md](../INSTALL.md)** - Installation guide (all platforms)
3. **[CONFIGURATION.md](../CONFIGURATION.md)** - Configuration and setup
4. **[USAGE.md](../USAGE.md)** - Complete CLI command reference
5. **[FAQ.md](../FAQ.md)** - Common questions and troubleshooting

### For Developers

Start here if you want to contribute or extend RMAgent:

1. **[DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)** - Architecture, design patterns, API reference
2. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution workflow
3. **[TESTING.md](../TESTING.md)** - Testing guide
4. **[CHANGELOG.md](../CHANGELOG.md)** - Version history

### Additional Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive user guide (31KB, all-in-one)
- **[AGENTS.md](../AGENTS.md)** - Agent design patterns

---

## 📖 Documentation by Topic

### Installation & Setup

| Document | Description | Audience |
|----------|-------------|----------|
| [INSTALL.md](../INSTALL.md) | Platform-specific installation (macOS, Linux, Windows/WSL2) | All users |
| [CONFIGURATION.md](../CONFIGURATION.md) | Environment variables, LLM providers, prompt customization | All users |
| [FAQ.md](../FAQ.md) | Troubleshooting installation issues | All users |

### Using RMAgent

| Document | Description | Audience |
|----------|-------------|----------|
| [USAGE.md](../USAGE.md) | All 7 CLI commands with 50+ examples | All users |
| [USER_GUIDE.md](USER_GUIDE.md) | Comprehensive guide (installation → advanced usage) | All users |
| [FAQ.md](../FAQ.md) | Common workflows and troubleshooting | All users |

### Development

| Document | Description | Audience |
|----------|-------------|----------|
| [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) | Architecture, API reference, adding features | Developers |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Git workflow, coding standards, PR process | Contributors |
| [TESTING.md](../TESTING.md) | Test suite guide (279 tests, coverage analysis) | Developers |
| [CHANGELOG.md](../CHANGELOG.md) | Complete version history | All |

### Technical Reference

| Document | Description | Audience |
|----------|-------------|----------|
| [AGENTS.md](../AGENTS.md) | Agent design patterns | Developers |
| [data_reference/](../data_reference/) | RootsMagic 11 schema (18 docs) | Developers |

---

## 🎯 Quick Navigation

### By Task

**I want to...**

- **Install RMAgent** → [INSTALL.md](../INSTALL.md)
- **Configure API keys** → [CONFIGURATION.md](../CONFIGURATION.md) (LLM Provider Setup)
- **Generate a biography** → [USAGE.md](../USAGE.md) (Biography Command)
- **Customize prompts** → [CONFIGURATION.md](../CONFIGURATION.md) (Prompt Customization)
- **Run quality checks** → [USAGE.md](../USAGE.md) (Quality Command)
- **Export to Hugo** → [USAGE.md](../USAGE.md) (Export Command)
- **Fix errors** → [FAQ.md](../FAQ.md) (Troubleshooting)
- **Add a new feature** → [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) (Adding New Features)
- **Run tests** → [TESTING.md](../TESTING.md) (Running Tests)
- **Contribute code** → [CONTRIBUTING.md](../CONTRIBUTING.md) (Contribution Workflow)

### By Role

**New User:**
1. [README.md](../README.md) → [INSTALL.md](../INSTALL.md) → [CONFIGURATION.md](../CONFIGURATION.md) → [USAGE.md](../USAGE.md)

**Contributor:**
1. [README.md](../README.md) → [CONTRIBUTING.md](../CONTRIBUTING.md) → [TESTING.md](../TESTING.md)

**Developer (adding features):**
1. [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) → [CONTRIBUTING.md](../CONTRIBUTING.md) → [TESTING.md](../TESTING.md)

---

## 📦 Project Documentation Files

### Top-Level Documentation (8 files)

Located in project root:

```
RM11/
├── README.md              # Project overview & quick start
├── INSTALL.md             # Installation guide (515 lines)
├── USAGE.md               # CLI command reference (800+ lines)
├── CONFIGURATION.md       # Configuration guide (1,000+ lines)
├── FAQ.md                 # Common questions (550+ lines)
├── CONTRIBUTING.md        # Contribution guidelines (450+ lines)
├── TESTING.md             # Testing guide (600+ lines)
├── CHANGELOG.md           # Version history (350+ lines)
├── DEVELOPER_GUIDE.md     # Developer guide (1,000+ lines)
└── AGENTS.md              # Agent design patterns
```

**Total:** 5,865+ lines of documentation

### docs/ Directory

Project-specific documentation:

```
docs/
├── README.md              # This file - documentation index
├── USER_GUIDE.md          # Comprehensive user guide (1,424 lines)
├── MVP_CHECKPOINT.md      # Milestone 2 verification
├── PHASE_5_COMPLETION.md  # Testing & Quality report
├── PHASE_6_COMPLETION.md  # Documentation & Polish report
├── AI_AGENT_TODO.md       # Project roadmap
├── Test_Coverage_Analysis.md
├── INTEGRATION_TESTING_SUMMARY.md
├── REAL_API_VERIFICATION.md
└── OPTIMIZATION_SUMMARY.md
```

### data_reference/ Directory

RootsMagic 11 schema documentation (18 files):

```
data_reference/
├── RM11_Schema_Reference.md         # Complete schema
├── RM11_Date_Format.md              # 24-char date encoding
├── RM11_Place_Format.md             # Place hierarchy
├── RM11_FactTypes.md                # Event types
├── RM11_BLOB_*.md                   # XML BLOB specs (3 files)
├── RM11_Biography_Best_Practices.md # 9-section structure
├── RM11_Data_Quality_Rules.md       # 24 validation rules
├── RM11_Query_Patterns.md           # SQL patterns
├── RM11_Timeline_Construction.md    # TimelineJS3 format
└── ... (10 more reference docs)
```

---

## 🔍 Documentation Statistics

**Total Documentation:**
- **Lines:** 7,289+ lines
- **Files:** 36 files (10 top-level + 10 docs/ + 16 data_reference/)
- **Coverage:** Installation, usage, configuration, development, schema, API

**By Category:**
- **User Documentation:** 3,500+ lines (INSTALL, USAGE, CONFIGURATION, FAQ, USER_GUIDE)
- **Developer Documentation:** 2,050+ lines (DEVELOPER_GUIDE, CONTRIBUTING, TESTING)
- **Project Documentation:** 1,200+ lines (CHANGELOG, completion reports, roadmap)
- **Schema Reference:** 18 files (data_reference/)

---

## 📝 Documentation Updates

### Recent Updates (v0.2.0 - October 12, 2025)

**New Documentation:**
- ✅ **DEVELOPER_GUIDE.md** - Comprehensive developer guide with architecture, API reference, adding features
- ✅ **Prompt Customization** - Complete section in CONFIGURATION.md with YAML examples
- ✅ **USER_GUIDE.md** - Updated to v0.2.0 with new prompt system

**Updated Documentation:**
- ✅ USER_GUIDE.md - "Customizing Prompts" section updated for YAML system
- ✅ CONFIGURATION.md - Added 350+ line "Prompt Customization" section
- ✅ CHANGELOG.md - Phase 5 and Phase 6 entries

### Version History

- **v0.2.0** (2025-10-12): Phase 5 & 6 complete - Testing, Quality, Documentation
- **v0.1.0** (2025-10-10): MVP complete - All 8 CLI commands working
- **v0.0.3** (2025-10-09): Milestone 1 - Working prototype

---

## 🤝 Contributing to Documentation

Documentation improvements are always welcome!

**To contribute documentation:**

1. **Small fixes:** Edit directly and submit PR
2. **New sections:** Open issue first to discuss
3. **Style guide:** Follow existing format
4. **Examples:** Include practical code examples
5. **Testing:** Verify all commands work

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## 📞 Getting Help

**Questions about documentation:**
- Open an issue: https://github.com/miams/rmagent/issues
- Discussions: https://github.com/miams/rmagent/discussions

**Found a bug in documentation:**
- Report it: https://github.com/miams/rmagent/issues
- Include: Which file, what's wrong, suggested fix

---

**Last Updated:** October 12, 2025
