import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

// Generiert eine einfache, zufällige ID -- reicht für unseren Zweck völlig
function generateThreadId() {
  return "thread-" + Math.random().toString(36).substring(2, 15);
}

const FEATURES = [
  "Fragen zum Video-Inhalt",
  "Zusammenfassung anfordern (allgemein oder detailliert)",
  "Fakten-Check von Aussagen",
  "Zeitstempel-Suche (z.B. 'was wurde bei Minute 20 gesagt')",
  "Video-Infos (Titel, Kanal, Länge)",
  "Erweiterte Suche bei komplexen Fragen",
];

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // useState mit einer Funktion als Startwert: wird nur EINMAL beim ersten Rendern ausgeführt,
  // nicht bei jedem Neu-Rendern -- genau das, was wir wollen (eine ID pro Sitzung)
  const [threadId, setThreadId] = useState(() => generateThreadId());

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleAsk = async () => {
    const currentQuestion = question;
    setMessages((prev) => [...prev, { role: "user", content: currentQuestion }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(
        "https://health-fitness-qa-bot-backend.onrender.com/ask",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: currentQuestion, thread_id: threadId }),
        },
      );
      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Fehler: Backend nicht erreichbar." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setThreadId(generateThreadId());
    setQuestion("");
    setMessages([]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Health/Fitness QA-Bot</h1>
        <button className="btn btn-secondary" onClick={handleNewChat}>
          Neuer Chat
        </button>
      </header>

      {messages.length === 0 && (
        <section className="features" aria-label="Was du fragen kannst">
          <ul className="features-list">
            {FEATURES.map((feature) => (
              <li key={feature} className="feature-chip">
                {feature}
              </li>
            ))}
          </ul>
        </section>
      )}

      <main className="chat-area">
        {messages.length === 0 && !loading && (
          <p className="chat-empty">
            Stell eine Frage zum Video, um loszulegen.
          </p>
        )}

        {messages.map((message, index) => {
          const isError = message.content.startsWith("Fehler:");
          return (
            <div
              key={index}
              className={
                message.role === "user"
                  ? "message message-user"
                  : isError
                    ? "message message-assistant message-error"
                    : "message message-assistant"
              }
            >
              {message.role === "assistant" ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : (
                message.content
              )}
            </div>
          );
        })}

        {loading && (
          <div className="message message-assistant message-loading">
            <span className="typing-dots" aria-label="Antwort wird geladen">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </span>
          </div>
        )}

        <div ref={chatEndRef} />
      </main>

      <footer className="input-bar">
        <textarea
          className="input-textarea"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Stell eine Frage zum Video..."
          rows={2}
        />
        <button
          className="btn btn-primary"
          onClick={handleAsk}
          disabled={loading || !question}
        >
          Senden
        </button>
      </footer>
    </div>
  );
}

export default App;
