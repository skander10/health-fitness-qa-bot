import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import Sidebar from "./components/Sidebar";
import Hub from "./components/Hub";
import "./App.css";

const API_BASE_URL = "https://health-fitness-qa-bot-backend.onrender.com";
const CONVERSATIONS_STORAGE_KEY = "hf-qa-bot-conversations";

// Generiert eine einfache, zufällige ID -- reicht für unseren Zweck völlig
function generateThreadId() {
  return "thread-" + Math.random().toString(36).substring(2, 15);
}

function formatConversationLabel(topic) {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, "0");
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  return `${topic} — ${day}.${month}. ${hours}:${minutes}`;
}

function loadConversationsFromStorage() {
  try {
    const raw = localStorage.getItem(CONVERSATIONS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function App() {
  const [view, setView] = useState("chat"); // "chat" | "hub"

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // useState mit einer Funktion als Startwert: wird nur EINMAL beim ersten Rendern ausgeführt,
  // nicht bei jedem Neu-Rendern -- genau das, was wir wollen (eine ID pro Sitzung)
  const [threadId, setThreadId] = useState(() => generateThreadId());

  const [topics, setTopics] = useState([]);
  const [activeTopic, setActiveTopic] = useState(null);
  const [videos, setVideos] = useState([]);
  const [activeVideoId, setActiveVideoId] = useState(null);
  const [videosByTopic, setVideosByTopic] = useState({});

  const [conversations, setConversations] = useState(() =>
    loadConversationsFromStorage(),
  );
  const [previewConversation, setPreviewConversation] = useState(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Topics einmalig laden
  useEffect(() => {
    fetch(`${API_BASE_URL}/topics`)
      .then((res) => res.json())
      .then((data) => setTopics(data.topics || []))
      .catch(() => setTopics([]));
  }, []);

  // Sobald Topics geladen sind, Standard-Topic setzen (falls noch keins gewählt wurde)
  useEffect(() => {
    if (!activeTopic && topics.length > 0) {
      setActiveTopic(topics[0]);
    }
  }, [topics, activeTopic]);

  // Videos für das aktive Topic laden (für die Sidebar), Cache für die Hub-Seite mitfüllen
  useEffect(() => {
    if (!activeTopic) return;
    fetch(`${API_BASE_URL}/topics/${activeTopic}/videos`)
      .then((res) => res.json())
      .then((data) => {
        const vids = data.videos || [];
        setVideos(vids);
        setVideosByTopic((prev) => ({ ...prev, [activeTopic]: vids }));
      })
      .catch(() => setVideos([]));
  }, [activeTopic]);

  // Auf der Hub-Seite: Videos für alle Topics laden, die noch nicht im Cache sind
  useEffect(() => {
    if (view !== "hub") return;
    const missing = topics.filter((topic) => !videosByTopic[topic]);
    missing.forEach((topic) => {
      fetch(`${API_BASE_URL}/topics/${topic}/videos`)
        .then((res) => res.json())
        .then((data) => {
          setVideosByTopic((prev) => ({ ...prev, [topic]: data.videos || [] }));
        })
        .catch(() => {
          setVideosByTopic((prev) => ({ ...prev, [topic]: [] }));
        });
    });
  }, [view, topics, videosByTopic]);

  const ensureConversationSaved = (savedThreadId, topic, videoId) => {
    setConversations((prev) => {
      if (prev.some((c) => c.threadId === savedThreadId)) return prev;
      const next = [
        {
          threadId: savedThreadId,
          topic,
          videoId: videoId ?? null,
          label: formatConversationLabel(topic),
        },
        ...prev,
      ];
      localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const updateConversationExchange = (
    savedThreadId,
    lastQuestion,
    lastAnswer,
  ) => {
    setConversations((prev) => {
      const next = prev.map((c) =>
        c.threadId === savedThreadId ? { ...c, lastQuestion, lastAnswer } : c,
      );
      localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const handleAsk = async () => {
    if (!activeTopic || !question) return;
    const currentQuestion = question;
    const currentTopic = activeTopic;
    const currentVideoId = activeVideoId;
    const currentThreadId = threadId;

    ensureConversationSaved(currentThreadId, currentTopic, currentVideoId);

    setPreviewConversation(null);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: currentQuestion },
    ]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: currentQuestion,
          thread_id: currentThreadId,
          topic: currentTopic,
          video_id: currentVideoId,
        }),
      });
      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
      updateConversationExchange(currentThreadId, currentQuestion, data.answer);
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
    setPreviewConversation(null);
    setView("chat");
  };

  const selectTopic = (topic) => {
    if (topic === activeTopic) return;
    setActiveTopic(topic);
    setActiveVideoId(null);
    setThreadId(generateThreadId());
    setMessages([]);
    setQuestion("");
    setPreviewConversation(null);
  };

  const switchVideo = (videoId) => {
    if (videoId === activeVideoId) return;
    setActiveVideoId(videoId);
    setThreadId(generateThreadId());
    setMessages([]);
    setQuestion("");
    setPreviewConversation(null);
  };

  const startChatFromHub = (topic, videoId) => {
    setActiveTopic(topic);
    setActiveVideoId(videoId ?? null);
    setThreadId(generateThreadId());
    setMessages([]);
    setQuestion("");
    setPreviewConversation(null);
    setView("chat");
  };

  const handleSelectConversation = (conv) => {
    setActiveTopic(conv.topic);
    setActiveVideoId(conv.videoId ?? null);
    setThreadId(conv.threadId);
    setMessages([]);
    setQuestion("");
    setView("chat");
    setPreviewConversation(conv.lastQuestion || conv.lastAnswer ? conv : null);
  };

  const activeVideoTitle = activeVideoId
    ? (videos.find((v) => v.video_id === activeVideoId)?.title ?? activeVideoId)
    : null;

  return (
    <div className="layout">
      <Sidebar
        topics={topics}
        activeTopic={activeTopic}
        onSelectTopic={selectTopic}
        videos={videos}
        activeVideoId={activeVideoId}
        onSelectVideo={switchVideo}
        onSelectAllVideos={() => switchVideo(null)}
        conversations={conversations}
        activeThreadId={threadId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onGoToHub={() => setView("hub")}
      />

      <div className="app">
        {view === "hub" ? (
          <Hub
            topics={topics}
            videosByTopic={videosByTopic}
            onStartChat={startChatFromHub}
            onBack={() => setView("chat")}
          />
        ) : (
          <div className="app-content">
            <header className="app-header">
              <p className="app-context">
                {activeTopic ?? "Lade Thema…"}
                {activeVideoId
                  ? ` · ${activeVideoTitle}`
                  : activeTopic
                    ? " · Alle Videos"
                    : ""}
              </p>
            </header>

            <main className="chat-area">
              {previewConversation && messages.length === 0 && (
                <div className="conversation-preview">
                  <p className="conversation-preview-label">
                    Letzter Austausch in diesem Gespräch:
                  </p>
                  <p className="conversation-preview-question">
                    {previewConversation.lastQuestion}
                  </p>
                  <p className="conversation-preview-answer">
                    {previewConversation.lastAnswer}
                  </p>
                </div>
              )}

              {messages.length === 0 && !loading && !previewConversation && (
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
                  <span
                    className="typing-dots"
                    aria-label="Antwort wird geladen"
                  >
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
                disabled={loading || !question || !activeTopic}
              >
                Senden
              </button>
            </footer>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
