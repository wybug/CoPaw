import { useState, useEffect, useCallback } from "react";
import { Card, Button, Empty, Spin, message, Tag } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import api from "../../../api";
import type { HubSkillSpec } from "../../../api/types";
import styles from "./index.module.less";

interface SkillsStoreTabProps {
  searchQuery: string;
}

function SkillsStoreTab({ searchQuery }: SkillsStoreTabProps) {
  const { t } = useTranslation();
  const [skills, setSkills] = useState<HubSkillSpec[]>([]);
  const [loading, setLoading] = useState(false);
  const [installing, setInstalling] = useState<Set<string>>(new Set());

  const searchSkills = useCallback(async (query: string) => {
    setLoading(true);
    try {
      const results = await api.searchHubSkills(query || "", 50);
      // Ensure results is an array
      if (Array.isArray(results)) {
        setSkills(results);
      } else {
        console.warn("searchHubSkills returned non-array:", results);
        setSkills([]);
      }
    } catch (error) {
      console.error("Failed to search skills:", error);
      message.error(t("enterpriseStore.searchFailed", "Search failed"));
      setSkills([]);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const timer = setTimeout(() => {
      searchSkills(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, searchSkills]);

  const handleInstall = async (skill: HubSkillSpec) => {
    if (installing.has(skill.slug)) return;

    setInstalling((prev) => new Set(prev).add(skill.slug));
    try {
      await api.installHubSkill({
        bundle_url: skill.source_url,
        enable: true,
      });
      message.success(t("enterpriseStore.installSuccess", { name: skill.name }));
    } catch (error) {
      console.error("Failed to install skill:", error);
      message.error(t("enterpriseStore.installFailed", { name: skill.name }));
    } finally {
      setInstalling((prev) => {
        const next = new Set(prev);
        next.delete(skill.slug);
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

  if (skills.length === 0) {
    return (
      <Empty
        description={searchQuery ? t("enterpriseStore.noResults") : t("enterpriseStore.noSkills")}
        className={styles.emptyState}
      />
    );
  }

  return (
    <div className={styles.storeGrid}>
      {skills.map((skill) => (
        <Card
          key={skill.slug}
          className={styles.storeCard}
          hoverable
          actions={[
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={installing.has(skill.slug)}
              onClick={() => handleInstall(skill)}
            >
              {installing.has(skill.slug)
                ? t("enterpriseStore.installing")
                : t("enterpriseStore.install")}
            </Button>,
          ]}
        >
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>{skill.name}</h3>
            {skill.version && (
              <Tag className={styles.versionTag}>{skill.version}</Tag>
            )}
          </div>
          <p className={styles.cardDescription}>{skill.description}</p>
          <div className={styles.cardMeta}>
            <Tag>{skill.slug}</Tag>
          </div>
        </Card>
      ))}
    </div>
  );
}

export { SkillsStoreTab };
