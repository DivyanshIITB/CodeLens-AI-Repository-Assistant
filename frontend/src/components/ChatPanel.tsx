import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ExternalLink, Loader2, Sparkles, Square, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAppStore } from '../store/useAppStore';
import { streamChat } from '../services/api';
import { Citation, ChatMessage } from '../types';

export const ChatPanel: React.FC = () => {
  const {
    activeRepo,
    chatMessages,
    setChatMessages,
    selectedModel,
    settings,
    loadFileContent,
    setActiveCitations
  } = useAppStore();

  const [input, setInput] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeRepo || isStreaming) return;

    const userQuery = input.trim();
    setInput('');

    const userMsgId = Date.now().toString();
    const aiMsgId = (Date.now() + 1).toString();

    const userMsg: ChatMessage = { id: userMsgId, sender: 'user', text: userQuery };
    const initialAiMsg: ChatMessage = { id: aiMsgId, sender: 'ai', text: '', citations: [], isStreaming: true };

    setChatMessages(prev => [...prev, userMsg, initialAiMsg]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let accumulatedText = '';

    await streamChat(
      {
        repo_id: activeRepo.id,
        message: userQuery,
        model: selectedModel,
        top_k: settings.top_k,
        temperature: settings.temperature
      },
      (citations, confidenceScore, confidenceLevel) => {
        setActiveCitations(citations);
        setChatMessages(prev =>
          prev.map(msg =>
            msg.id === aiMsgId
              ? {
                  ...msg,
                  citations,
                  confidence_score: confidenceScore,
                  confidence_level: confidenceLevel
                }
              : msg
          )
        );
      },
      (token) => {
        accumulatedText += token;
        setChatMessages(prev =>
          prev.map(msg => (msg.id === aiMsgId ? { ...msg, text: accumulatedText } : msg))
        );
      },
      (durationMs) => {
        setIsStreaming(false);
        abortControllerRef.current = null;
        setChatMessages(prev =>
          prev.map(msg => (msg.id === aiMsgId ? { ...msg, isStreaming: false, duration_ms: durationMs } : msg))
        );
      },
      (err) => {
        setIsStreaming(false);
        abortControllerRef.current = null;
        if (err.name === 'AbortError') {
          setChatMessages(prev =>
            prev.map(msg =>
              msg.id === aiMsgId
                ? {
                    ...msg,
                    isStreaming: false,
                    text: accumulatedText + '\n\n⏹️ *Generation stopped by user.*'
                  }
                : msg
            )
          );
        } else {
          setChatMessages(prev =>
            prev.map(msg =>
              msg.id === aiMsgId
                ? {
                    ...msg,
                    isStreaming: false,
                    text: accumulatedText + '\n\n⚠️ *Connection error or local Ollama service unavailable.*'
                  }
                : msg
            )
          );
        }
      },
      controller.signal
    );
  };

  if (!activeRepo) {
    return (
      <div className="flex-1 bg-github-dark flex flex-col items-center justify-center p-8 text-center">
        <Bot className="w-16 h-16 text-github-muted mb-4 animate-bounce" />
        <h2 className="text-xl font-bold text-white mb-2">No Active Repository</h2>
        <p className="text-sm text-github-muted max-w-md mb-6">
          Import a GitHub repository URL or upload a local project ZIP archive to start asking architectural and code questions.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-github-dark flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-3 max-w-4xl ${
              msg.sender === 'user' ? 'ml-auto flex-row-reverse space-x-reverse' : ''
            }`}
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gradient-to-tr from-purple-600 to-blue-600 text-white shadow-md'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className="space-y-3 flex-1">
              <div
                className={`p-4 rounded-xl border text-sm leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-blue-950/40 border-blue-800/50 text-white'
                    : 'bg-github-panel border-github-border text-github-text shadow-sm'
                }`}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  className="prose prose-invert max-w-none text-sm space-y-2"
                >
                  {msg.text || (msg.isStreaming ? 'Searching repository vectors & generating answer...' : '')}
                </ReactMarkdown>

                {msg.isStreaming && !msg.text && (
                  <div className="flex items-center space-x-2 text-xs text-github-accent mt-2 animate-pulse">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing code AST and streaming response tokens...</span>
                  </div>
                )}

                <div className="mt-3 pt-2 border-t border-github-border/40 text-[11px] text-github-muted flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {msg.sender === 'ai' && msg.confidence_score !== undefined && (
                      <div className="flex items-center space-x-1 font-mono font-medium">
                        <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                        <span>RAG Confidence:</span>
                        <ConfidenceBadge score={msg.confidence_score} level={msg.confidence_level || 'Moderate'} />
                      </div>
                    )}
                    <span>Generated via {selectedModel}</span>
                  </div>
                  {msg.duration_ms && <span>{(msg.duration_ms / 1000).toFixed(2)}s</span>}
                </div>
              </div>

              {msg.citations && msg.citations.length > 0 && (
                <div className="bg-github-dark border border-github-border rounded-lg p-3 space-y-2">
                  <div className="text-xs font-semibold text-github-accent flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Retrieved Source Citations ({msg.citations.length})</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {msg.citations.map((cit, i) => (
                      <div
                        key={i}
                        onClick={() => loadFileContent(activeRepo.id, cit.file_path, [cit.start_line, cit.end_line])}
                        className="bg-github-panel hover:bg-github-hover border border-github-border hover:border-github-accent rounded-md p-2.5 cursor-pointer transition text-xs group"
                      >
                        <div className="flex items-center justify-between font-mono text-github-accent group-hover:text-blue-300 font-medium truncate">
                          <span className="truncate">{cit.file_path}</span>
                          <ExternalLink className="w-3 h-3 shrink-0 ml-1 opacity-60 group-hover:opacity-100" />
                        </div>
                        <div className="text-[11px] text-github-muted flex items-center justify-between mt-1">
                          <span>Lines {cit.start_line}-{cit.end_line}</span>
                          <span className="uppercase text-[10px] bg-github-dark px-1 rounded border border-github-border">
                            {cit.chunk_type}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="p-4 border-t border-github-border bg-github-panel">
        <div className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            placeholder={`Ask CodeLens AI about ${activeRepo.name} (e.g., "Where is authentication handled?")`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
            className="w-full bg-github-dark border border-github-border rounded-xl pl-4 pr-24 py-3 text-sm text-white focus:outline-none focus:border-github-accent placeholder-github-muted shadow-inner"
          />
          {isStreaming ? (
            <button
              type="button"
              onClick={handleStop}
              className="absolute right-2 bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition shadow"
              title="Stop Generation"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="absolute right-2 bg-github-accent hover:bg-blue-600 disabled:opacity-40 text-white p-2 rounded-lg transition"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

const ConfidenceBadge: React.FC<{ score: number; level: string }> = ({ score, level }) => {
  let badgeColor = 'bg-emerald-950/80 text-emerald-400 border-emerald-700/60';
  if (score < 60) {
    badgeColor = 'bg-red-950/80 text-red-400 border-red-700/60';
  } else if (score < 80) {
    badgeColor = 'bg-amber-950/80 text-amber-400 border-amber-700/60';
  }

  return (
    <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold border ${badgeColor}`}>
      {score}% ({level})
    </span>
  );
};
