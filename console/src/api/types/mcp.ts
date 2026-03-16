/**
 * MCP (Model Context Protocol) client types
 */

export interface MCPClientInfo {
  /** Unique client key identifier */
  key: string;
  /** Client display name */
  name: string;
  /** Client description */
  description: string;
  /** Whether the client is enabled */
  enabled: boolean;
  /** MCP transport type */
  transport: "stdio" | "streamable_http" | "sse";
  /** Remote MCP endpoint URL for HTTP/SSE transport */
  url: string;
  /** HTTP headers for remote transport */
  headers: Record<string, string>;
  /** Command to launch the MCP server */
  command: string;
  /** Command-line arguments */
  args: string[];
  /** Environment variables */
  env: Record<string, string>;
  /** Working directory for stdio command */
  cwd: string;
}

export interface MCPClientCreateRequest {
  /** Unique client key identifier */
  client_key: string;
  /** Client configuration */
  client: {
    /** Client display name */
    name: string;
    /** Client description */
    description?: string;
    /** Whether to enable the client */
    enabled?: boolean;
    /** MCP transport type */
    transport?: "stdio" | "streamable_http" | "sse";
    /** Remote MCP endpoint URL for HTTP/SSE transport */
    url?: string;
    /** HTTP headers for remote transport */
    headers?: Record<string, string>;
    /** Command to launch the MCP server */
    command?: string;
    /** Command-line arguments */
    args?: string[];
    /** Environment variables */
    env?: Record<string, string>;
    /** Working directory for stdio command */
    cwd?: string;
  };
}

export interface MCPClientUpdateRequest {
  /** Client display name */
  name?: string;
  /** Client description */
  description?: string;
  /** Whether to enable the client */
  enabled?: boolean;
  /** MCP transport type */
  transport?: "stdio" | "streamable_http" | "sse";
  /** Remote MCP endpoint URL for HTTP/SSE transport */
  url?: string;
  /** HTTP headers for remote transport */
  headers?: Record<string, string>;
  /** Command to launch the MCP server */
  command?: string;
  /** Command-line arguments */
  args?: string[];
  /** Environment variables */
  env?: Record<string, string>;
  /** Working directory for stdio command */
  cwd?: string;
}

/**
 * Hub MCP server types
 */

export interface HubMCPServerSpec {
  /** Unique server slug identifier */
  slug: string;
  /** Server display name */
  name: string;
  /** Server description */
  description: string;
  /** Server version */
  version: string;
  /** MCP transport type */
  transport: "stdio" | "streamable_http" | "sse";
  /** Command to launch the MCP server */
  command?: string;
  /** Command-line arguments */
  args?: string[];
  /** Remote MCP endpoint URL for HTTP/SSE transports */
  url?: string;
  /** Environment variables */
  env_vars?: Record<string, string>;
  /** HTTP headers for remote transport */
  headers?: Record<string, string>;
  /** Working directory for stdio command */
  cwd?: string;
  /** Enterprise signature */
  signature?: string;
}

export interface HubMCPServerResult {
  /** Server slug */
  slug: string;
  /** Server name */
  name: string;
  /** Server description */
  description: string;
  /** Server version */
  version: string;
  /** Transport type */
  transport: string;
  /** Source URL */
  source_url: string;
}

export interface InstallHubMCPServerRequest {
  /** Server slug to install */
  slug: string;
  /** Whether to enable after installation */
  enable?: boolean;
}
