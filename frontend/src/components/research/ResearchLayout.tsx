import React from "react";

interface ResearchLayoutProps {
  header: React.ReactNode;
  sidebar: React.ReactNode;
  detail: React.ReactNode;
}

export const ResearchLayout: React.FC<ResearchLayoutProps> = ({ header, sidebar, detail }) => {
  return (
    <div>
      {header}
      <div style={{ display: "grid", gridTemplateColumns: "360px minmax(0, 1fr)", gap: "20px", alignItems: "start" }}>
        <aside style={{ minWidth: 0 }}>{sidebar}</aside>
        <main style={{ minWidth: 0 }}>{detail}</main>
      </div>
    </div>
  );
};
