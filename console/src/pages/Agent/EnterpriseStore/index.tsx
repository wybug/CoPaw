import { useState } from "react";
import { Tabs, Input } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { SkillsStoreTab } from "./SkillsStoreTab";
import { MCPStoreTab } from "./MCPStoreTab";
import styles from "./index.module.less";

function EnterpriseStorePage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"skills" | "mcp">("skills");
  const [searchQuery, setSearchQuery] = useState("");

  const handleTabChange = (key: string) => {
    setActiveTab(key as "skills" | "mcp");
    setSearchQuery("");
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  return (
    <div className={styles.enterpriseStorePage}>
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h1 className={styles.title}>{t("enterpriseStore.title")}</h1>
          <p className={styles.description}>
            {t("enterpriseStore.description")}
          </p>
        </div>
        <div className={styles.searchBar}>
          <Input
            placeholder={t("enterpriseStore.searchPlaceholder")}
            prefix={<SearchOutlined />}
            value={searchQuery}
            onChange={handleSearchChange}
            allowClear
            className={styles.searchInput}
          />
        </div>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        className={styles.storeTabs}
        items={[
          {
            key: "skills",
            label: t("enterpriseStore.skillsStore"),
            children: (
              <SkillsStoreTab searchQuery={searchQuery} />
            ),
          },
          {
            key: "mcp",
            label: t("enterpriseStore.mcpStore"),
            children: (
              <MCPStoreTab searchQuery={searchQuery} />
            ),
          },
        ]}
      />
    </div>
  );
}

export default EnterpriseStorePage;
