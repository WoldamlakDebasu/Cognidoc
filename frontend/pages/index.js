import Head from 'next/head';
import { useState, useCallback } from 'react';

export default function Home() {
  const [documents, setDocuments] = useState([]);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = useCallback(async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const res = await fetch('http://localhost:8000/upload/', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to upload documents.');
      }

      const data = await res.json();
      setDocuments(prevDocs => [...prevDocs, ...data.uploaded_files]);
      alert('Documents uploaded and processed successfully!');
    } catch (err) {
      setError(err.message);
      console.error('Upload error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleQuerySubmit = useCallback(async (event) => {
    event.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setResponse(null);
    setError(null);

    try {
      const res = await fetch('http://localhost:8000/query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to get response from AI.');
      }

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err.message);
      console.error('Query error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [query]);

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <Head>
        <title>CogniDocs: Enterprise RAG Engine</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white shadow p-4">
        <h1 className="text-3xl font-bold text-center text-gray-800">CogniDocs: Enterprise RAG Engine</h1>
        <p className="text-center text-gray-600 mt-2">Intelligent Answers from Your Enterprise Data</p>
      </header>

      <main className="flex-grow container mx-auto p-6 flex">
        {/* Left Sidebar - Document Management */}
        <aside className="w-1/4 bg-white p-4 rounded-lg shadow-md mr-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Knowledge Base</h2>
          <label htmlFor="file-upload" className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200 block text-center mb-4">
            {isLoading ? 'Uploading...' : '+ Upload Documents'}
          </label>
          <input
            id="file-upload"
            type="file"
            multiple
            className="hidden"
            onChange={handleFileUpload}
            disabled={isLoading}
          />

          <div className="space-y-2">
            {documents.length === 0 && <p className="text-gray-500 text-sm">No documents uploaded yet.</p>}
            {documents.map((doc, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
                <span className="text-gray-800 text-sm truncate">{doc}</span>
                <span className="text-green-500 text-xs font-medium">Ready</span>
              </div>
            ))}
            {/* Pre-loaded sample documents */}
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
              <span className="text-gray-800 text-sm truncate">Tesla_2023_10K_Report.pdf</span>
              <span className="text-green-500 text-xs font-medium">Ready</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md border border-gray-200">
              <span className="text-gray-800 text-sm truncate">Technical_Manual_Model-X.pdf</span>
              <span className="text-green-500 text-xs font-medium">Ready</span>
            </div>
          </div>
        </aside>

        {/* Right Section - Chat Interface */}
        <section className="flex-grow bg-white p-6 rounded-lg shadow-md flex flex-col">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">AI Assistant</h2>

          <div className="flex-grow border border-gray-200 rounded-md p-4 overflow-y-auto mb-4 bg-gray-50">
            {!response && !error && (
              <p className="text-gray-600 italic">I am an AI assistant trained on the documents in this knowledge base. Ask me a complex question about the provided materials.</p>
            )}
            {error && (
              <div className="text-red-600">
                <p className="font-bold">Error:</p>
                <p>{error}</p>
              </div>
            )}
            {response && (
              <div>
                <p className="text-gray-800 mb-2"><strong>Your Query:</strong> {query}</p>
                <p className="text-gray-800 mb-4"><strong>AI Response:</strong> {response.answer}</p>
                {response.sources && response.sources.length > 0 && (
                  <div className="mt-2">
                    <details className="cursor-pointer text-blue-600 hover:underline">
                      <summary>Sources ({response.sources.length})</summary>
                      <ul className="list-disc list-inside text-gray-700 text-sm mt-1">
                        {response.sources.map((source, idx) => (
                          <li key={idx}>{source.document} (Page {source.page_number})</li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}
              </div>
            )}
            {isLoading && <p className="text-blue-600 italic">Thinking...</p>}
          </div>

          <form onSubmit={handleQuerySubmit} className="flex">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-grow p-3 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-3 rounded-r-md hover:bg-blue-700 transition-colors duration-200"
              disabled={isLoading}
            >
              Ask AI
            </button>
          </form>
        </section>
      </main>

      <footer className="bg-gray-800 text-white text-center p-4 mt-6">
        <p>&copy; 2025 CogniDocs. Powered by Woldamlak AI.</p>
      </footer>
    </div>
  );
}


