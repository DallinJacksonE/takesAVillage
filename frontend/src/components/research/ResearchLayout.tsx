import React from "react";

import styles from "./ResearchLayout.module.css";
interface ResearchLayoutProps {
  header: React.ReactNode;
  sidebar: React.ReactNode;
  detail: React.ReactNode;
}

export const ResearchLayout: React.FC<ResearchLayoutProps> = ({ header, sidebar, detail }) => {
  return (
    <div>
      {header}
      <div className={styles.panel}>
        <aside className={styles.rail}>{sidebar}</aside>
        <main className={styles.main}>{detail}</main>
      </div>
    </div>
  );
};
