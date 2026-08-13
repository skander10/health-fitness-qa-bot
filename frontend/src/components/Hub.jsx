import { useState } from "react";

const TOPIC_DESCRIPTIONS = {
  health: "Health & Nutrition Videos",
};

function NutrientBar({ label, grams, pct, className }) {
  return (
    <div className="nutrient-bar-row">
      <span className="nutrient-bar-label">{label}</span>
      <div className="nutrient-bar-track">
        <div
          className={`nutrient-bar-fill ${className}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="nutrient-bar-value">
        {grams}g ({pct}%)
      </span>
    </div>
  );
}

function RecipeSummaryModal({ loading, error, data, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Nährwert-Übersicht</h3>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Schließen"
          >
            ×
          </button>
        </div>

        {loading && (
          <div className="loading-indicator">
            <span className="typing-dots" aria-label="Rezept wird analysiert">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </span>
            <span>Analysiere Rezept…</span>
          </div>
        )}

        {error && (
          <p className="modal-error">
            Fehler beim Laden der Nährwert-Übersicht.
          </p>
        )}

        {data && !data.has_recipe && (
          <p className="modal-empty">Kein Rezept in diesem Video erkannt.</p>
        )}

        {data && data.has_recipe && (
          <div className="recipe-summary">
            <div className="recipe-summary-section">
              <h4 className="recipe-summary-heading">Zutaten</h4>
              <ul className="recipe-summary-list">
                {data.ingredients.map((ingredient, i) => (
                  <li key={i}>{ingredient}</li>
                ))}
              </ul>
            </div>

            <div className="recipe-summary-section">
              <h4 className="recipe-summary-heading">Zubereitung</h4>
              <ol className="recipe-summary-list">
                {data.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>

            <div className="recipe-summary-section">
              <h4 className="recipe-summary-heading">
                Nährwerte (geschätzt pro Portion)
              </h4>
              <p className="recipe-summary-calories">
                {data.calories_kcal} kcal
              </p>

              <NutrientBar
                label="Protein"
                grams={data.protein_g}
                pct={data.protein_pct}
                className="nutrient-bar-protein"
              />
              <NutrientBar
                label="Kohlenhydrate"
                grams={data.carbs_g}
                pct={data.carbs_pct}
                className="nutrient-bar-carbs"
              />
              <NutrientBar
                label="Fett"
                grams={data.fat_g}
                pct={data.fat_pct}
                className="nutrient-bar-fat"
              />

              <p className="recipe-summary-sugar">
                davon Zucker: {data.sugar_g}g
              </p>
            </div>

            <div className="recipe-summary-section">
              <h4 className="recipe-summary-heading">Einschätzung</h4>
              <p>{data.health_verdict}</p>
            </div>

            <p className="recipe-summary-disclaimer">{data.disclaimer}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Hub({ topics, videosByTopic, onStartChat, onBack, apiBaseUrl }) {
  const [activeSummaryVideoId, setActiveSummaryVideoId] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(false);

  const handleShowSummary = async (videoId) => {
    setActiveSummaryVideoId(videoId);
    setSummaryData(null);
    setSummaryError(false);
    setSummaryLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/videos/${videoId}/recipe-summary`);
      const data = await response.json();
      setSummaryData(data);
    } catch (error) {
      setSummaryError(true);
    } finally {
      setSummaryLoading(false);
    }
  };

  const closeSummary = () => {
    setActiveSummaryVideoId(null);
    setSummaryData(null);
    setSummaryError(false);
  };

  return (
    <div className="hub">
      <header className="hub-header">
        <h2 className="app-title">Alle Topics</h2>
        <button type="button" className="btn btn-secondary" onClick={onBack}>
          Zurück zum Chat
        </button>
      </header>

      {topics.length === 0 && (
        <div className="loading-indicator">
          <span className="typing-dots" aria-label="Themen werden geladen">
            <span className="typing-dot"></span>
            <span className="typing-dot"></span>
            <span className="typing-dot"></span>
          </span>
          <span>Lade Themen…</span>
        </div>
      )}

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
                  <div className="hub-video-card-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => onStartChat(topic, video.video_id)}
                    >
                      Chat starten
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => handleShowSummary(video.video_id)}
                    >
                      Nährwert-Übersicht
                    </button>
                  </div>
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

      {activeSummaryVideoId && (
        <RecipeSummaryModal
          loading={summaryLoading}
          error={summaryError}
          data={summaryData}
          onClose={closeSummary}
        />
      )}
    </div>
  );
}

export default Hub;
