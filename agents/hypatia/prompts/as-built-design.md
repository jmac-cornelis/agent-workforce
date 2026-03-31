# Hypatia - As-Built Design Prompt

You are generating an `as_built` or `engineering_reference` document.
Your task is to analyze actual source code and produce architecture and design documentation that is strictly grounded in what exists, not what is aspirational.

## 3-Pass Analysis Methodology

You must perform a 3-pass analysis of the provided source files before generating the final document.

### PASS 1: Structure Discovery
- Read all source files in the target module or directory.
- Group the files by module boundary (NOT individual files).
- For each module extract:
  - **Module ID**: The identifier for the module.
  - **Layer**: Categorize as handler, service, model, utility, or integration.
  - **Capability**: A compressed name for what the module does (use capability names, not class names).
  - **Responsibility**: Exactly one sentence describing what the module is responsible for.
  - **Dependencies**: List of other module IDs this module depends on.
  - **Design patterns detected**: Any standard patterns used (e.g., Factory, Singleton, Strategy).
- **Compression Rule**: Use capability names, not class names. Keep descriptions to one sentence per responsibility.

### PASS 2: Behavior Tracing
- Trace key flows through the module.
- Prioritize: data flows, error flows, and integration flows.
- For each flow, extract:
  - **Flow name**: A descriptive name for the interaction.
  - **Mermaid sequence diagram**: The interaction sequence.
  - **External calls**: Systems or external APIs called during the flow.
  - **Error boundaries**: Where errors are caught, handled, or propagated.
- **Limit**: Maximum 3 to 5 flows per module.

### PASS 3: Synthesis
- Generate the final document using the structure defined below.

## Final Document Structure

Your output must be formatted in Markdown and contain the following sections in this exact order:

1. **Module Overview**
   - One paragraph summarizing the module's overall purpose and scope.

2. **Component Diagram**
   - A Mermaid component diagram illustrating the module structure.
   - Limit to 5 to 12 components maximum.

3. **Key Flows**
   - Document the top 3 flows identified in Pass 2.
   - Each flow must include a Mermaid sequence diagram and a brief text description.

4. **Data Model**
   - Describe the core data structures, state, or database schemas used by the module (if applicable).

5. **Dependencies**
   - A table listing internal and external dependencies.
   - Columns: `| Dependency | Purpose | Version |`

6. **Configuration**
   - Document environment variables, configuration files, and feature flags required by the module.

7. **Error Handling**
   - Describe the error handling patterns and the exception hierarchy used.

8. **Known Limitations / Technical Debt**
   - Document any hardcoded values, missing implementations, or areas for improvement.

## Anti-patterns to Flag
If you detect any of the following during your analysis, you must explicitly flag them in the 'Known Limitations / Technical Debt' section:
- God classes (>500 lines with >10 public methods)
- Circular dependencies between modules or classes
- Missing error handling on external calls or I/O boundaries
- Hardcoded credentials or URLs

## Output Constraints
- All output must be valid Markdown.
- Use single quotes for inline code references (e.g., 'my_function()').
- Preserve any module header comments found in the source code.
- Ensure all claims are strictly backed by the provided source files.
