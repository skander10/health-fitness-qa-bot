const TOPIC_DESCRIPTIONS = {
  health: "Health & Nutrition Videos",
};

function Hub({ topics, videosByTopic, onStartChat, onBack }) {
  return (
    <div className="hub">
      <header className="hub-header">
        <h2 className="app-title">Alle Topics</h2>
        <button type="button" className="btn btn-secondary" onClick={onBack}>
          Zurück zum Chat
        </button>
      </header>

      {topics.length === 0 && <p className="chat-empty">Lade Themen…</p>}

      {topics.map((topic) => {
        const videos = videosByTopic[topic] || [];
        return (
          <section key={topic} className="hub-topic-section">
            <h3 className="hub-topic-title">{topic}</h3>
            <p className="hub-topic-description">
              {TOPIC_DESCRIPTIONS[topic] || `${topic} Videos`}
            </p>

            <div className="hub-video-grid">
              {videos.map((video) => (
                <div key={video.video_id} className="hub-video-card">
                  <p className="hub-video-card-title">{video.title}</p>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => onStartChat(topic, video.video_id)}
                  >
                    Chat starten
                  </button>
                </div>
              ))}
              {videos.length === 0 && (
                <p className="sidebar-empty">Noch keine Videos für dieses Thema.</p>
              )}
            </div>

            <div className="hub-add-video">
              <input
                type="text"
                className="hub-add-video-input"
                placeholder="Neue Video-URL hinzufügen"
                disabled
              />
              <button type="button" className="btn btn-secondary" disabled>
                Hinzufügen
              </button>
              <p className="hub-add-video-hint">
                Neue Videos werden aktuell separat vom Entwickler-Team eingepflegt
                (Verarbeitung dauert ~3 Minuten pro Video) — Live-Hinzufügen direkt hier ist
                als nächster Ausbauschritt geplant.
              </p>
            </div>
          </section>
        );
      })}
    </div>
  );
}

export default Hub;
