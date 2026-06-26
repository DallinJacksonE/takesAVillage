import React, { useState } from "react";

interface ExpandableJsonPanelProps {
  title: string;
  data: unknown;
}

export const ExpandableJsonPanel: React.FC<ExpandableJsonPanelProps> = ({ title, data }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <section style={{ marginTop: "18px", border: "1px solid #ddd", borderRadius: "6px", overflow: "hidden" }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{ width: "100%", padding: "10px", textAlign: "left", border: 0, background: "#f7f7f7", cursor: "pointer", fontWeight: 600 }}
      >
        {isOpen ? "▾" : "▸"} {title}
      </button>
      {isOpen && (
        <pre style={{ margin: 0, padding: "12px", maxHeight: "520px", overflow: "auto", background: "#111", color: "#f7f7f7" }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </section>
  );
};
