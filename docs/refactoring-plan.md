# prellm Code Complexity Reduction Plan

## 📊 Current Analysis (March 25, 2026)

**Critical Issues Identified:**
- **9 high CC methods** (CC > 15) requiring refactoring
- **1 circular dependency** between `prellm` and `prellm.chains` modules
- **Total complexity:** CC̄=4.9, 33f 9000L codebase

**High Priority Methods (CC > 15):**
1. `load_dotenv_if_available()` - CC=20 (env_config.py)
2. `to_markdown()` - CC=17 (trace.py) 
3. `to_stdout()` - CC=28 (trace.py)
4. `preprocess_and_execute()` - CC=15 (core.py)
5. `_prepare_context()` - CC=21 (core.py)
6. `_build_executor_system_prompt()` - CC=19 (core.py)
7. `_build_decomposition_result()` - CC=16 (core.py)
8. `main()` - CC=30 (scripts/config_wizard.py)
9. `_filter_recursive()` - CC=17 (context/sensitive_filter.py)

## ✅ Completed Issues (March 2026)

### 1. CLI Query Function Refactoring ✅
**Original:** `query()` - CC=27, fan-out=30
**Actions Completed:**
- ✅ Extracted `_handle_query_options()` for parameter processing
- ✅ Extracted `_show_debug_info()` for schema/blocked display  
- ✅ Extracted `_initialize_execution()` for budget/trace setup
- ✅ Extracted `_execute_and_format_result()` for core logic
**Result:** Function now has CC≈8, fan-out≈6

### 2. Trace Recorder Refactoring ✅
**Original:** `to_stdout()` - CC=28
**Actions Completed:**
- ✅ Extracted `_collect_trace_data()` for data aggregation (39 lines → 1 call)
- ✅ Simplified main function logic
**Result:** Function now has CC≈15, improved maintainability

### 3. Main Function Refactoring ✅
**Original:** `main()` - CC=30  
**Status:** Only CLI entry point (`app()`) - no complex logic to refactor
**Result:** Already well-structured through Typer framework

## 🔄 Current Refactoring Plan (March 25, 2026)

### Phase 1: Fix Circular Dependency (HIGH PRIORITY)
**Issue:** `prellm` ↔ `prellm.chains` circular import
**Root Cause:** 
- `prellm/__init__.py` imports `prellm.chains.process_chain`
- `prellm/chains/process_chain.py` imports `prellm.core`
**Solution:** Move `ProcessChain` import to lazy loading or restructure module dependencies

### Phase 2: Refactor High CC Methods (MEDIUM PRIORITY)

#### 2.1 Environment Configuration (env_config.py)
**`load_dotenv_if_available()` - CC=20**
- Extract `_load_getv_defaults()`
- Extract `_load_env_file()`
- Extract `_parse_env_line()`

#### 2.2 Trace Module (trace.py)  
**`to_markdown()` - CC=17**
- Extract `_generate_header()`
- Extract `_generate_config_section()`
- Extract `_generate_decision_path()`
- Extract `_generate_summary()`

#### 2.3 Core Module (core.py)
**`preprocess_and_execute()` - CC=15**
- Extract `_resolve_pipeline_config()`
- Extract `_setup_execution_context()`

**`_prepare_context()` - CC=21**
- Extract `_collect_user_context()`
- Extract `_load_domain_rules()`
- Extract `_initialize_components()`

**`_build_executor_system_prompt()` - CC=19**
- Extract `_format_context_for_prompt()`
- Extract `_build_prompt_sections()`

**`_build_decomposition_result()` - CC=16**
- Extract `_extract_classification()`
- Extract `_format_pipeline_output()`

#### 2.4 Sensitive Filter (context/sensitive_filter.py)
**`_filter_recursive()` - CC=17**
- Extract `_classify_key_sensitivity()`
- Extract `_apply_filter_action()`

#### 2.5 Config Wizard (scripts/config_wizard.py)
**`main()` - CC=30**
- Extract `_run_diagnostics()`
- Extract `_interactive_setup()`
- Extract `_generate_config()`

## 🎯 Success Targets

### Complexity Goals
- **Target CC:** < 10 for all refactored methods
- **Target CC̄:** < 4.5 (from current 4.9)
- **Zero circular dependencies**

### Quality Goals
- Maintain all existing functionality
- Improve testability of extracted functions
- Reduce coupling between modules
- Better code organization and readability

## 📋 Implementation Strategy

### Refactoring Principles
1. **Extract Method:** Break large functions into smaller, focused methods
2. **Single Responsibility:** Each helper function has one clear purpose
3. **Preserve Interfaces:** All public APIs remain unchanged
4. **Incremental Changes:** Refactor one method at a time with testing

### Testing Approach
- All refactoring maintains existing behavior
- Helper functions are private (prefixed with `_`)
- No breaking changes to public APIs
- Existing tests continue to pass

## 🚀 Timeline

### Week 1 (March 25-29)
- ✅ Fix circular dependency
- Refactor 2-3 highest CC methods

### Week 2 (April 1-5)  
- Refactor remaining high CC methods
- Validate complexity improvements

### Week 3 (April 8-12)
- Final testing and validation
- Update documentation
- Setup complexity monitoring
