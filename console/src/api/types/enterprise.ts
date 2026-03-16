/**
 * Enterprise Store types
 */

export interface HubSkillResult {
  /** Skill slug */
  slug: string;
  /** Skill name */
  name: string;
  /** Skill description */
  description: string;
  /** Skill version */
  version: string;
  /** Source URL */
  source_url: string;
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

export type StoreType = "skills" | "mcp";

export interface StoreSearchResult {
  type: StoreType;
  skills?: HubSkillResult[];
  mcpServers?: HubMCPServerResult[];
}
