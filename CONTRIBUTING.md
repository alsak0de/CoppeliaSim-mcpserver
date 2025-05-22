# Contributing to the CoppeliaSim MCP Server

Thank you for your interest in contributing! This project follows the Model Context Protocol (MCP) standards for tools, prompts, and resources. Please read the following guidelines carefully to ensure your additions are compliant, discoverable, and robust.

---

## Project Structure Overview

- `coppelia_mcp.py`, `coppelia_fastmcp.py`: Main server entry points.
- `prompts.py`: All prompt definitions and prompt logic.
- `resources.py`: All resource definitions and resource reading logic.
- `docs/`: Documentation files and usage guides exposed as resources.
- `robot/`: Robot-specific backend logic (e.g., describe.py).

---

## Adding a New Tool

### 1. Tool Definition (MCP Standard)
Each tool must be defined as an object with the following properties:
- `name`: string, unique identifier for the tool.
- `description`: (optional) human-readable description.
- `inputSchema`: object, JSON Schema defining the tool's parameters.
  - `type`: must be "object"
  - `properties`: object, defines each parameter with its type and constraints.
  - `required`: array of strings, lists required parameters.
- `annotations`: (optional) object, provides metadata:
  - `title`: (optional) human-readable title.
  - `readOnlyHint`: (optional) true if the tool does not modify state.
  - `destructiveHint`: (optional) true if the tool may perform destructive actions.
  - `idempotentHint`: (optional) true if repeated calls with the same arguments have no additional effect.
  - `openWorldHint`: (optional) true if the tool interacts with external entities.

### 2. Tool Implementation
- Implement the tool logic in the appropriate server file or a backend module (e.g., `robot/`).
- Register the tool in the server (using the FastMCP decorator or by adding to the tools list in FastAPI).
- Validate all input parameters against the defined `inputSchema`.
- Ensure the tool is discoverable via the `tools/list` method and callable via `tools/call`.
- Add or update the tool's entry in the server's tool list, following the MCP structure.

### 3. Security and Best Practices
- Validate all input parameters to prevent injection attacks or unintended behavior.
- Use annotations to describe tool behavior (e.g., destructive, idempotent).
- Provide clear, concise descriptions and argument documentation.
- Only expose tools that are safe and necessary for model/agent use.

---

## Adding a New Resource

### 1. Resource Definition (MCP Standard)
- Add a new entry to `RESOURCE_LIST` in `resources.py`:
  - `uri`: unique resource URI (e.g., `local:///docs/my_guide.txt`)
  - `name`: human-readable label
  - `description`: (optional) description of the resource
  - `mimeType`: (optional) MIME type (e.g., `text/plain`, `application/json`)
- Only include resources that actually exist in the project (e.g., in `docs/`).
- For new documentation, create the file in the `docs/` directory.

### 2. Resource Discovery and Reading
- The resource will be discoverable via the `resources/list` method.
- The content will be accessible via the `resources/read` method.
- For binary resources, ensure content is base64-encoded and `mimeType` is set appropriately.

### 3. Resource Templates (Optional)
- For dynamic or parameterized resources, add a `uriTemplate` entry following RFC 6570.

### 4. Best Practices
- Use clear, descriptive names and URIs.
- Keep documentation and guides up to date.
- Only list resources that are useful and accessible to clients/LLMs.

---

## Adding a New Prompt

### 1. Prompt Definition (MCP Standard)
- Add a new prompt object to the `PROMPTS` list in `prompts.py`:
  - `name`: string, unique identifier for the prompt
  - `description`: (optional) human-readable description
  - `arguments`: (optional) array of argument definitions (name, description, required)
  - `messages`: array of message objects, each with:
    - `role`: "system", "user", or "assistant"
    - `content`: object with:
      - `type`: "text" or "resource"
      - If `type` is "text":
        - `text`: string (may use argument interpolation)
      - If `type` is "resource":
        - `resource`: object with `uri`, `text`, and `mimeType`

### 2. Prompt Usage
- Prompts are discoverable via the `prompts/list` method.
- Prompts can be retrieved and used via the `prompts/get` method, with arguments if required.
- Use system messages to provide context for the LLM.
- Include multiple user phrasings for robust intent recognition.

### 3. Best Practices
- Be verbose and explicit in descriptions and messages.
- Use natural language and synonyms to cover a wide range of user intents.
- Keep prompts up to date with the server's capabilities and tools.

---

## Server Capabilities Declaration
- Ensure the server declares its capabilities in the `initialize` response, including:
  - `tools`: if tools are supported
  - `resources`: with `subscribe` and/or `listChanged` if supported

---

## Security and Compliance
- Validate all user input and arguments.
- Only expose safe, necessary tools and resources.
- Regularly review and update definitions for compatibility and security.

---

## Example: Adding a New Tool
1. Implement the tool logic in `robot/` or the main server file.
2. Add the tool definition to the server's tool list, following the MCP schema.
3. Register the tool for discovery and invocation.
4. Add a prompt for the tool in `prompts.py` if user interaction is expected.
5. (Optional) Add a resource (e.g., usage guide) in `docs/` and list it in `resources.py`.

---

For any questions or to propose major changes, please open an issue or discussion first. Thank you for helping make this MCP server robust, compliant, and LLM-friendly! 