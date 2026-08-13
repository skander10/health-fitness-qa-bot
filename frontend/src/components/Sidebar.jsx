import { useState } from "react";

const FEATURES = [
  "Fragen zum Video-Inhalt",
  "Zusammenfassung anfordern (allgemein oder detailliert)",
  "Fakten-Check von Aussagen",
  "Zeitstempel-Suche (z.B. 'was wurde bei Minute 20 gesagt')",
  "Video-Infos (Titel, Kanal, Länge)",
  "Erweiterte Suche bei komplexen Fragen",
];

function CollapsibleSection({ title, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="sidebar-section">
      <button
        type="button"
        className="sidebar-section-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span>{title}</span>
        <span className="sidebar-section-caret">{open ? "−" : "+"}</span>
      </button>
      {open && <div className="sidebar-section-body">{children}</div>}
    </div>
  );
}

function Sidebar({
  topics,
  activeTopic,
  onSelectTopic,
  videos,
  videosLoading,
  activeVideoId,
  onSelectVideo,
  onSelectAllVideos,
  conversations,
  activeThreadId,
  onSelectConversation,
  onNewChat,
  onGoToHub,
}) {
  return (
    <aside className="sidebar">
      <h1 className="app-title">Health/Fitness QA-Bot</h1>

      <button type="button" className="sidebar-hub-link" onClick={onGoToHub}>
        Alle Topics
      </button>

      <CollapsibleSection title="Themen">
        {topics.length === 0 ? (
          <div className="loading-indicator">
            <span className="typing-dots" aria-label="Themen werden geladen">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </span>
            <span>Lade Themen…</span>
          </div>
        ) : (
          <ul className="sidebar-list">
            {topics.map((topic) => (
              <li key={topic}>
                <button
                  type="button"
                  className={
                    "sidebar-list-item sidebar-list-item-topic" +
                    (topic === activeTopic ? " sidebar-list-item-active" : "")
                  }
                  onClick={() => onSelectTopic(topic)}
                >
                  {topic}
                </button>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleSection>

      <CollapsibleSection title="Videos">
        {videosLoading ? (
          <div className="loading-indicator">
            <span className="typing-dots" aria-label="Videos werden geladen">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </span>
            <span>Lade Videos…</span>
          </div>
        ) : (
          <ul className="sidebar-list">
            <li>
              <button
                type="button"
                className={
                  "sidebar-list-item" +
                  (activeVideoId == null ? " sidebar-list-item-active" : "")
                }
                onClick={onSelectAllVideos}
              >
                Alle Videos dieses Themas
              </button>
            </li>
            {videos.map((video) => (
              <li key={video.video_id}>
                <button
                  type="button"
                  className={
                    "sidebar-list-item" +
                    (video.video_id === activeVideoId ? " sidebar-list-item-active" : "")
                  }
                  onClick={() => onSelectVideo(video.video_id)}
                >
                  {video.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleSection>

      <CollapsibleSection title="Funktionen">
        <ul className="features-list">
          {FEATURES.map((feature) => (
            <li key={feature} className="feature-chip">
              {feature}
            </li>
          ))}
        </ul>
      </CollapsibleSection>

      <CollapsibleSection title="Gespräche">
        <button
          type="button"
          className="btn btn-secondary sidebar-new-chat"
          onClick={onNewChat}
        >
          Neuer Chat
        </button>
        {conversations.length === 0 && (
          <p className="sidebar-empty">Noch keine gespeicherten Gespräche.</p>
        )}
        <ul className="sidebar-list">
          {conversations.map((conv) => (
            <li key={conv.threadId}>
              <button
                type="button"
                className={
                  "sidebar-list-item" +
                  (conv.threadId === activeThreadId ? " sidebar-list-item-active" : "")
                }
                onClick={() => onSelectConversation(conv)}
              >
                {conv.label}
              </button>
            </li>
          ))}
        </ul>
      </CollapsibleSection>
    </aside>
  );
}

export default Sidebar;
