"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Code, Eye, MessageSquare, Sparkles, Loader2 } from "lucide-react";
import Editor from "@monaco-editor/react";

interface Message {
  id: string;
  content: string;
  timestamp: Date;
  imageData?: string;
  generatedHtml?: string;
}

const API_URL = "http://localhost:8000";

export default function Home() {
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [currentInput, setCurrentInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeTab, setActiveTab] = useState<"code" | "preview">("preview");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const isValidUrl = (urlString: string): boolean => {
    try {
      new URL(urlString);
      return true;
    } catch (e) {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentInput.trim()) return;

    // Reset error state
    setError(null);

    // Validate URL
    if (!isValidUrl(currentInput)) {
      setError("Please enter a valid URL (e.g., https://example.com)");
      return;
    }

    setIsLoading(true);

    try {
      // Call the screenshot API
      const response = await fetch(`${API_URL}/screenshot`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: currentInput,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to capture screenshot: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Failed to capture screenshot");
      }

      const newMessage: Message = {
        id: Date.now().toString(),
        content: currentInput,
        timestamp: new Date(),
        imageData: data.image_data,
        generatedHtml: data.generated_html,
      };

      setMessages([...messages, newMessage]);
      setHasSubmitted(true);
      setCurrentInput("");
      setActiveTab("preview"); // Switch to preview tab automatically
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const selectMessage = (message: Message) => {
    // When selecting a message from history, show its screenshot
    setActiveTab("preview");
    // Don't set the input if we're loading
    if (!isLoading) {
      setCurrentInput(message.content);
    }
  };

  if (!hasSubmitted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen bg-black flex items-center justify-center p-8"
      >
        <div className="w-full max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-center mb-8"
          >
            <div className="flex items-center justify-center mb-6">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-3 rounded-2xl">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
              Enter a URL to clone
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              We'll generate the HTML code to recreate any webpage
            </p>
          </motion.div>

          <motion.form
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            onSubmit={handleSubmit}
            className="relative"
          >
            <div className="relative">
              <input
                ref={inputRef}
                type="url"
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                placeholder="https://example.com"
                className="w-full bg-gray-900/50 border border-gray-700 rounded-2xl px-6 py-4 pr-14 text-white placeholder-gray-400 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent backdrop-blur-sm"
              />
              <button
                type="submit"
                disabled={!currentInput.trim() || isLoading}
                className="absolute right-3 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-xl p-2 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Send className="w-5 h-5 text-white" />
                )}
              </button>
            </div>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-red-500 mt-2 text-sm"
              >
                {error}
              </motion.p>
            )}
          </motion.form>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mt-8 text-center"
          >
            <p className="text-sm text-gray-500">
              Press Enter to capture screenshot
            </p>
          </motion.div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-screen bg-black flex"
    >
      {/* Left Sidebar */}
      <motion.div
        initial={{ x: -300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="w-80 bg-gray-900 border-r border-gray-800 flex flex-col"
      >
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-semibold text-white">Generated Pages</h2>
          </div>
          
          <form onSubmit={handleSubmit} className="relative">
            <input
              type="url"
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              placeholder="Enter URL..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 pr-10 text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={!currentInput.trim() || isLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded p-1 transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-3 h-3 text-white animate-spin" />
              ) : (
                <Send className="w-3 h-3 text-white" />
              )}
            </button>
          </form>
          {error && (
            <p className="text-red-500 mt-2 text-xs">{error}</p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => selectMessage(message)}
                className="p-3 bg-gray-800 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors group"
              >
                <div className="flex items-start gap-2">
                  <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5 group-hover:text-blue-400 transition-colors" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm line-clamp-2 group-hover:text-blue-100 transition-colors">
                      {message.content}
                    </p>
                    <p className="text-gray-500 text-xs mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Right Content Area */}
      <motion.div
        initial={{ x: 300, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: "spring", damping: 25, stiffness: 200, delay: 0.1 }}
        className="flex-1 flex flex-col"
      >
        {/* Tab Header */}
        <div className="bg-gray-900 border-b border-gray-800 p-4">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === "preview"
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <Eye className="w-4 h-4" />
              Preview
            </button>
            <button
              onClick={() => setActiveTab("code")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === "code"
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <Code className="w-4 h-4" />
              HTML
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 relative">
          <AnimatePresence mode="wait">
            {activeTab === "preview" && messages.length > 0 ? (
              <motion.div
                key="preview"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="h-full bg-gray-100 flex flex-col"
              >
                {messages[messages.length - 1].generatedHtml ? (
                  <>
                    <div className="p-4 bg-gray-900 border-b border-gray-800 flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400 text-sm">Scale:</span>
                          <select 
                            className="bg-gray-800 text-white text-sm rounded-lg px-2 py-1 border border-gray-700"
                            onChange={(e) => {
                              const iframe = document.querySelector('#preview-iframe') as HTMLIFrameElement;
                              if (iframe) {
                                iframe.style.transform = `scale(${e.target.value})`;
                              }
                            }}
                          >
                            <option value="1">100%</option>
                            <option value="0.75">75%</option>
                            <option value="0.5">50%</option>
                          </select>
                        </div>
                        <div className="h-4 w-px bg-gray-700" />
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400 text-sm">Width:</span>
                          <select 
                            className="bg-gray-800 text-white text-sm rounded-lg px-2 py-1 border border-gray-700"
                            onChange={(e) => {
                              const container = document.querySelector('#iframe-container') as HTMLDivElement;
                              if (container) {
                                container.style.width = e.target.value;
                              }
                            }}
                          >
                            <option value="100%">Full</option>
                            <option value="1440px">Desktop</option>
                            <option value="1024px">Tablet</option>
                            <option value="375px">Mobile</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 overflow-auto bg-gray-800 p-8">
                      <div 
                        id="iframe-container"
                        className="mx-auto bg-white shadow-2xl transition-all duration-200"
                        style={{ width: '100%' }}
                      >
                        <iframe
                          id="preview-iframe"
                          srcDoc={messages[messages.length - 1].generatedHtml}
                          className="w-full h-[calc(100vh-12rem)] bg-white transition-transform duration-200 origin-top"
                          style={{ transform: 'scale(1)' }}
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-500">
                    Waiting for HTML generation...
                  </div>
                )}
              </motion.div>
            ) : activeTab === "code" && messages.length > 0 ? (
              <motion.div
                key="code"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="h-full"
              >
                <Editor
                  height="100%"
                  defaultLanguage="html"
                  value={messages[messages.length - 1].generatedHtml || "// Analyzing webpage and generating HTML code..."}
                  theme="vs-dark"
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: "on",
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: "on",
                    readOnly: true,
                  }}
                />
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex items-center justify-center text-gray-500"
              >
                Enter a URL to see the generated code
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </motion.div>
  );
}
