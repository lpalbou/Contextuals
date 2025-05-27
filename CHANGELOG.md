# Changelog

All notable changes to the Contextuals library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-26

### 🎯 Major Features Added

#### Enhanced "All" Mode with Complete Context
- **Completed `contextuals all` command** with previously missing information
- **Added system information**: OS details, hardware specs, memory usage, disk space
- **Added user information**: Current user, language settings, environment details  
- **Added machine information**: Hostname, architecture, platform specifics
- **Enhanced CLI**: `contextuals system`, `contextuals user`, `contextuals machine` commands
- **Comprehensive context**: Now provides complete environmental awareness for AI applications

#### New "Simple" Mode for LLM Integration
- **Created `contextuals simple` command** optimized for LLM prompts
- **Structured data format**: Clean, consistent JSON/Markdown output
- **LLM-friendly**: Designed specifically for AI system prompts and context injection
- **Dual output formats**: JSON (default) and Markdown support
- **Programmatic access**: `get_simple_context()`, `get_simple_context_json()`, `get_simple_context_markdown()`

#### Minified JSON Support
- **Added `--minified` flag** for both `all` and `simple` commands
- **Size reduction**: 20-25% smaller JSON output for bandwidth/token efficiency
- **Programmatic support**: `minified=True` parameter in all JSON methods
- **Production ready**: Optimized for API calls and token-constrained environments

#### AI-Optimized Prompt System
- **Created `contextuals prompt` command** with 5 specialized variants
- **DEFAULT prompt**: Comprehensive context with detailed formatting (~128 tokens)
- **STRUCTURED prompt**: Clean JSON-like format with essential data (~53 tokens) - **WINNER**
- **COMPACT prompt**: Ultra-efficient context in minimal space (~28 tokens)
- **MINIMAL prompt**: Essential context only (~20 tokens)
- **DETAILED prompt**: Rich comprehensive context (~219 tokens)
- **Programmatic access**: `get_context_prompt_*()` methods for each variant

### 🔬 Comprehensive Benchmarking System

#### Empirical Testing Framework
- **Built comprehensive benchmark suite** testing 7 different language models
- **Multi-perspective evaluation**: LLM-as-a-judge with 3 scoring dimensions
  - Contextual Awareness: Use of environmental context
  - Accuracy & Relevance: Correctness and relevance to questions
  - Practical Utility: Usefulness and actionability
- **Model categories tested**: SLM (1B-3B), MLM (8B-12B), LLM (30B+)
- **Thinking capability detection**: Identified models with reasoning capabilities

#### Models Benchmarked
- **Small Language Models (SLM)**: granite3.3:2b, cogito:3b, gemma3:1b
- **Medium Language Models (MLM)**: granite3.3:8b, cogito:8b, gemma3:12b  
- **Large Language Models (LLM)**: qwen3:30b-a3b-q4_K_M (with thinking capabilities)

#### Key Benchmark Findings
- **STRUCTURED prompt variant emerges as winner** with 8.21/10 average score
- **qwen3:30b-a3b-q4_K_M demonstrates superior performance** across all metrics
- **Thinking capabilities provide significant advantages** when available
- **Contextual prompts provide measurable benefits** across all model sizes
- **Token efficiency matters**: STRUCTURED offers best quality-efficiency balance

#### Benchmark Infrastructure
- **ModelBenchmark class**: `from contextuals import ModelBenchmark`
- **CLI interface**: `python -m contextuals.benchmarks.cli [models...]`
- **Results analysis**: `from contextuals.benchmarks import analyze_results`
- **Comprehensive documentation**: Complete results in `docs/BENCHMARK.md`
- **Detailed result files**: Individual model responses and metrics saved

### 📊 Evidence-Based Recommendations

Based on empirical testing across 7 models with 11 contextual questions:

#### **🏆 Best Overall Quality**
- **STRUCTURED prompt variant** (8.21/10 average score)
- **Usage**: `context.get_context_prompt_structured()`
- **Best for**: Production applications requiring high-quality contextual understanding

#### **🚀 Best Speed-Quality Balance** 
- **DEFAULT prompt variant** (36.35 tokens/sec)
- **Usage**: `context.get_context_prompt()`
- **Best for**: Speed-critical applications with moderate quality requirements

#### **💰 Most Token-Efficient**
- **COMPACT prompt variant** (7.17/10 score, ~28 tokens)
- **Usage**: `context.get_context_prompt_compact()`
- **Best for**: Token-constrained or cost-sensitive applications

#### **🎯 Recommended Model Combinations**
- **Premium Quality**: qwen3:30b-a3b-q4_K_M + STRUCTURED (8.5/10, thinking capabilities)
- **Production Balance**: gemma3:12b + STRUCTURED (8.67/10, good speed)
- **Speed Critical**: gemma3:1b + any variant (118.8 tokens/sec)
- **Reliable Choice**: granite3.3:8b + STRUCTURED (solid performance)

### 🛠️ Technical Improvements

#### Installation Options
- **Flexible installation**: `pip install contextuals[cli|benchmarks|full]`
- **Optional dependencies**: pydantic-ai for benchmarking capabilities
- **Package optimization**: Includes benchmark results, excludes unit tests

#### API Enhancements
- **Consistent JSON responses**: All methods return structured, timestamped data
- **Error handling**: Graceful fallbacks for missing data or API failures
- **Caching improvements**: Efficient TTL-based caching for all providers
- **Documentation**: Comprehensive examples and usage patterns

#### CLI Improvements
- **Enhanced help system**: Detailed help for all commands and options
- **Consistent formatting**: Pretty-print, JSON, and compact output modes
- **Error reporting**: Clear error messages and troubleshooting guidance

### 📚 Documentation

#### Comprehensive Documentation
- **README.md**: Updated with all new features and empirical recommendations
- **docs/BENCHMARK.md**: Complete benchmark report with detailed analysis
- **docs/PROMPT_TESTING_SUMMARY.md**: Detailed prompt variant analysis
- **Installation guide**: Multiple installation options and use cases
- **CLI reference**: Complete command documentation with examples

#### Evidence-Based Guidance
- **Empirical recommendations**: Based on actual testing, not theoretical analysis
- **Performance metrics**: Real-world speed and quality measurements
- **Use case guidance**: Specific recommendations for different application needs
- **Model selection**: Data-driven model and prompt combination advice

### 🔧 Breaking Changes
- None. All changes are backward compatible.

### 🐛 Bug Fixes
- Fixed missing system information in `get_all_context()` method
- Improved error handling for missing API keys
- Enhanced fallback mechanisms for offline usage

### 🚀 Performance Improvements
- Minified JSON reduces output size by 20-25%
- Optimized prompt variants for different speed/quality trade-offs
- Efficient caching reduces API calls and improves response times

---

## Development Notes

### Benchmarking Methodology
The benchmark system uses a rigorous methodology:
1. **11 contextual questions** covering weather, location, time, culture, system performance
2. **LLM-as-a-judge evaluation** using Qwen 3 30B for objective scoring
3. **Multi-perspective analysis** with three scoring dimensions
4. **Reproducible results** with detailed logging and result files
5. **Statistical analysis** with averages, confidence intervals, and insights

### Future Roadmap
- Expand benchmark to more models (70B+, different architectures)
- Add domain-specific contextual modules
- Implement real-time context streaming
- Add multi-language support for international contexts
- Develop context-aware conversation memory

---

*This changelog reflects the evolution of Contextuals from a basic contextual information library to a comprehensive, empirically-tested framework for context-aware AI applications.* 