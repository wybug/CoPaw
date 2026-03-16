import { useState, useEffect, useCallback } from "react";
import { Card, Button, Empty, Spin, message, Tag } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import type { HubMCPServerResult } from "../../../api/types/mcp";
import styles from "./index.module.less";

interface MCPStoreTabProps {
  searchQuery: string;
}

function MCPStoreTab({ searchQuery }: MCPStoreTabProps) {
  const { t } = useTranslation();
  const [servers, setServers] = useState<HubMCPServerResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [installing, setInstalling] = useState<Set<string>>(new Set());

  const searchServers = useCallback(async (query: string) => {
    setLoading(true);
    try {
      const results = await api.searchHubMCPServers(query || "", 50);
      // Ensure results is an array
      if (Array.isArray(results)) {
        setServers(results);
      } else {
        console.warn("searchHubMCPServers returned non-array:", results);
        setServers([]);
      }
    } catch (error) {
      console.error("Failed to search MCP servers:", error);
      message.error(t("enterpriseStore.searchFailed", "Search failed"));
      setServers([]);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const timer = setTimeout(() => {
      searchServers(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, searchServers]);

  const handleInstall = async (server: HubMCPServerResult) => {
    if (installing.has(server.slug)) return;

    setInstalling((prev) => new Set(prev).add(server.slug));
    try {
      await api.installHubMCPServer({
        slug: server.slug,
        enable: true,
      });
      message.success(t("enterpriseStore.installSuccess", { name: server.name }));
    } catch (error) {
      console.error("Failed to install MCP server:", error);
      message.error(t("enterpriseStore.installFailed", { name: server.name }));
    } finally {
      setInstalling((prev) => {
        const next = new Set(prev);
        next.delete(server.slug);
        return next;
      });
    }
  };

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <Spin size="large" />
      </div>
    );
  }

  if (servers.length === 0) {
    return (
      <Empty
        description={searchQuery ? t("enterpriseStore.noResults") : t("enterpriseStore.noMcpServers")}
        className={styles.emptyState}
      />
    );
  }

  return (
    <div className={styles.storeGrid}>
      {servers.map((server) => (
        <Card
          key={server.slug}
          className={styles.storeCard}
          hoverable
          actions={[
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={installing.has(server.slug)}
              onClick={() => handleInstall(server)}
            >
              {installing.has(server.slug)
                ? t("enterpriseStore.installing")
                : t("enterpriseStore.install")}
            </Button>,
          ]}
        >
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>{server.name}</h3>
            {server.version && (
              <Tag className={styles.versionTag}>{server.version}</Tag>
            )}
          </div>
          <p className={styles.cardDescription}>{server.description}</p>
          <div className={styles.cardMeta}>
            <Tag color="blue">{server.transport}</Tag>
            <Tag>{server.slug}</Tag>
          </div>
        </Card>
      ))}
    </div>
  );
}

export { MCPStoreTab };
